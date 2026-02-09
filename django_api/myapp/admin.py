from datetime import date, datetime
import sqlite3
from django.urls import path
from django.contrib import messages
from django.contrib import admin
from django.shortcuts import render, redirect
from django.utils.html import format_html

from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.credentials.services import generate_new_config_for_user
from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from .models import TelegramUser, Payment, Credential, Server
from .admin_forms import ImportLegacyUsersForm

admin.site.register(Payment)
admin.site.register(Credential)
admin.site.register(Server)


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
        OLD_DB_PATH = "/app/database.db"  # <-- ВАЖНО
        conn = sqlite3.connect(OLD_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                u.telegram_id,
                u.name,
                u.end_date,
                c.address
            FROM users u
            JOIN configs c ON c.user_id = u.user_id
            WHERE
                u.end_date IS NOT NULL
                AND u.is_unlimited = 0
            """
        )

        old_server = Server.objects.get(name__icontains="Old_server")
        imported_count = 0

        for telegram_id, name, end_date_str, ip in cursor.fetchall():
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except Exception:
                continue

            if end_date < active_after:
                continue

            user, created = TelegramUser.objects.get_or_create(
                telegram_id=int(telegram_id),
                defaults={
                    "name": name or f"user_{telegram_id}",
                    "end_date": end_date,
                },
            )

            if not created:
                user.end_date = end_date
                user.save()

            Credential.objects.get_or_create(
                user=user,
                defaults={
                    "wg_conf_ip": ip,
                    "wg_conf_old_server": True,
                },
            )

            imported_count += 1

        conn.close()
        return imported_count
