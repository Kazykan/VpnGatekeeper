from datetime import date
from django.urls import path
from django.contrib import messages
from django.contrib import admin
from django.shortcuts import render, redirect
from django.utils.html import format_html

from myapp.admin_actions import sync_vpn_user_action
from myapp.domain.infrastructure.legacy_importer import import_from_old_db
from myapp.tasks.broadcast import send_mass_message_task
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
    list_display = ("telegram_id", "name", "end_date", "is_gift")
    change_list_template = "admin/telegramuser_changelist.html"
    readonly_fields = (
        "sync_config_button_field",
        "generate_new_config_button",
    )  # добавляем поле в форму
    actions = ["send_mass_message"]  # Регистрируем действие

    @admin.display(description="VPN")
    def sync_action_link(self, obj):
        return format_html(
            '<a class="button" href="./{}/sync-vpn/">🔄 Sync</a>', obj.id
        )

    @admin.display(description="Действие")
    def sync_config_button_field(self, obj):
        if not obj.pk:
            return ""
        return format_html(
            '<a class="button" style="background-color: #447e9b; color: white;" '
            'href="/admin/myapp/telegramuser/{}/sync-vpn/">Обновить данные на серверах</a>',
            obj.id,
        )

    @admin.action(description="✉️ Рассылка сообщений")
    def send_mass_message(self, request, queryset):
        # 1. Если форма подтверждена (нажали кнопку "Запустить")
        if "confirm" in request.POST:
            message_text = request.POST.get("message_text")

            if not message_text:
                self.message_user(
                    request, "Ошибка: текст сообщения пуст", messages.ERROR
                )
                return

            # Получаем список ID из кверисета
            user_ids = list(queryset.values_list("id", flat=True))

            # Запускаем фоновую задачу Celery
            send_mass_message_task.delay(user_ids, message_text)  # type: ignore

            self.message_user(
                request, f"Рассылка для {len(user_ids)} пользователей запущена в фоне."
            )
            return redirect(request.get_full_path())

        # 2. Если действие только выбрано из списка, показываем промежуточную страницу
        return render(
            request,
            "admin/telegramuser/broadcast_confirmation.html",  # Путь относительно папки templates
            context={"queryset": queryset},
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-legacy/",
                self.admin_site.admin_view(self.import_legacy_users),
                name="import_legacy_users",
            ),
            path(
                "<int:user_id>/sync-vpn/",
                self.admin_site.admin_view(self.sync_vpn_handler),
                name="telegramuser-sync-vpn",
            ),
            path(
                "<int:user_id>/generate-new-config/",
                self.admin_site.admin_view(self.generate_new_config),
                name="telegramuser-generate-new-config",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Перевыпуск конфигурации")
    def generate_new_config_button(self, obj):
        if not obj.id:
            return ""

        if obj.end_date and obj.end_date >= date.today():
            return format_html(
                '<a class="button" style="margin-bottom: 5px;" href="{}">Создать новый конфиг</a>'
                '<br><br><small style="color: #666; display: block; line-height: 1.2; max-width: 250px;">'
                "⚠️ <b>Внимание:</b> удалит текущий конфиг Amnezia WG "
                "и создаст новый на VLESS серверах."
                "</small>",
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
                count = import_from_old_db(form.cleaned_data["active_after"])
                self.message_user(
                    request, f"Успешно импортировано: {count} пользователей"
                )
                return redirect("..")
        else:
            form = ImportLegacyUsersForm()
        return render(request, "admin/import_legacy_users.html", {"form": form})

    def sync_vpn_handler(self, request, user_id):
        user = self.get_object(request, user_id)
        # Вызываем логику из отдельного файла
        return sync_vpn_user_action(self, request, user)
