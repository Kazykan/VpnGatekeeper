from datetime import date, datetime
import sqlite3
from django.urls import path
from django.contrib import messages
from django.contrib import admin
from django.shortcuts import render, redirect
from django.utils.html import format_html

from myapp.tasks.provisioning import mass_sync_xray_credentials
from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.credentials.services import generate_new_config_for_user
from .models import TelegramUser, Payment, Credential, Server
from .admin_forms import ImportLegacyUsersForm

admin.site.register(Payment)


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_relay", "is_active")
    list_editable = ("is_active",)
    list_filter = ("is_active", "type")  # Удобный фильтр справа
    actions = ["trigger_mass_sync"]

    @admin.action(description="♻️ Обновить ключи ВСЕХ пользователей (массово)")
    def trigger_mass_sync(self, request, queryset):
        # Мы запускаем одну общую задачу
        mass_sync_xray_credentials.delay()  # type: ignore
        self.message_user(request, "Задача на массовое обновление запущена в фоне.")


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке
    list_display = ("user", "server", "active", "total_gb", "last_seen")

    # Фильтры справа (очень удобно фильтровать по серверу или статусу)
    list_filter = ("server", "active")

    # Поиск по имени пользователя или ID (используем __ для доступа к полям связанной модели)
    search_fields = ("user__name", "user__telegram_id", "client_email")

    # Если хотите, чтобы active можно было переключать прямо в списке:
    list_editable = ("active",)

    # Можно добавить отображение ваших @property методов
    @admin.display(description="Трафик (ГБ)")
    def total_gb_display(self, obj):
        return obj.total_gb


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "name", "end_date")
    change_list_template = "admin/telegramuser_changelist.html"
    readonly_fields = ("generate_new_config_button",)  # добавляем поле в форму

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-legacy/",
                self.admin_site.admin_view(self.import_legacy_users),
                name="import_legacy_users",
            ),
            path(
                "<int:user_id>/generate-new-config/",
                self.admin_site.admin_view(self.generate_new_config),
                name="telegramuser-generate-new-config",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Действие")
    def generate_new_config_button(self, obj):
        if not obj.id:
            return ""

        if obj.end_date and obj.end_date >= date.today():
            return format_html(
                '<a class="button" href="{}">Создать новый конфиг</a>',
                f"/admin/myapp/telegramuser/{obj.id}/generate-new-config/",
            )

        return "Нет активной подписки"

    def generate_new_config(self, request, user_id):
        user = TelegramUser.objects.get(id=user_id)

        try:
            generate_new_config_for_user(user)
            self.message_user(
                request,
                "Новый конфиг создается. Старый заблокирован.",
                messages.SUCCESS,
            )
        except NoActiveSubscription:
            self.message_user(
                request,
                "Ошибка: нет активной подписки",
                messages.ERROR,
            )

        return redirect(f"/admin/myapp/telegramuser/{user_id}/change/")

    def import_legacy_users(self, request):
        if request.method == "POST":
            form = ImportLegacyUsersForm(request.POST)
            if form.is_valid():
                active_after = form.cleaned_data["active_after"]

                imported = self._import_from_old_db(active_after)

                self.message_user(
                    request,
                    f"Импортировано пользователей: {imported}",
                )
                return redirect("..")
        else:
            form = ImportLegacyUsersForm()

        return render(
            request,
            "admin/import_legacy_users.html",
            {"form": form},
        )

    def _import_from_old_db(self, active_after):
        OLD_DB_PATH = "/app/database.db"
        conn = sqlite3.connect(OLD_DB_PATH)
        cursor = conn.cursor()

        # 1. LEFT JOIN позволяет взять всех пользователей, даже если у них нет конфига (ip будет None)
        cursor.execute(
            """
                SELECT
                    u.telegram_id,
                    u.name,
                    u.end_date,
                    c.address
                FROM users u
                LEFT JOIN configs c ON c.user_id = u.user_id
                WHERE u.is_unlimited = 0
                """
        )

        try:
            old_server = Server.objects.get(name__icontains="Old_server")
        except Server.DoesNotExist:
            old_server = None

        imported_count = 0

        for telegram_id, name, end_date_str, ip in cursor.fetchall():
            # Обработка даты
            current_end_date = None
            if end_date_str:
                try:
                    current_end_date = datetime.strptime(
                        end_date_str, "%Y-%m-%d"
                    ).date()
                except Exception:
                    current_end_date = None

            # ЛОГИКА ФИЛЬТРАЦИИ:
            # Если дата есть и она больше или равна active_after — это активный юзер
            is_active = current_end_date and current_end_date >= active_after

            # 2. Создаем или обновляем пользователя
            # Если юзер не активный по фильтру, записываем ему end_date = None (или оставляем старую, если хотите)
            target_date = current_end_date if is_active else None

            user, created = TelegramUser.objects.get_or_create(
                telegram_id=int(telegram_id),
                defaults={
                    "name": name or f"user_{telegram_id}",
                    "end_date": target_date,
                },
            )

            if not created:
                user.end_date = target_date
                user.save()

            # 3. Привязываем к серверу ТОЛЬКО активных пользователей, у которых есть IP
            if is_active and ip and old_server:
                Credential.objects.get_or_create(
                    user=user,
                    server=old_server,
                    defaults={
                        "wg_conf_ip": ip,
                        "wg_conf_old_server": True,
                    },
                )
            # Если юзер не активен, мы НЕ создаем Credential,
            # и он остается в БД просто как "клиент" без доступа.

            imported_count += 1

        conn.close()
        return imported_count
