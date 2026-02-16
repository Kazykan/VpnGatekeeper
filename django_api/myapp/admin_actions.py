# myapp/admin_actions.py
from django.contrib import messages
from django.shortcuts import redirect
from myapp.tasks.provisioning import sync_vpn_cluster


def sync_vpn_user_action(modeladmin, request, user):
    """
    Бизнес-логика вызова синхронизации из админки.
    """
    try:
        sync_vpn_cluster.delay(user.telegram_id) # type: ignore
        modeladmin.message_user(
            request,
            f"Синхронизация для {user.name} запущена. Параметры обновлены в 3x-ui.",
            messages.SUCCESS,
        )
    except Exception as e:
        modeladmin.message_user(
            request, f"Ошибка синхронизации: {str(e)}", messages.ERROR
        )

    return redirect(f"/admin/myapp/telegramuser/{user.id}/change/")
