from django.contrib import admin
from .models import TelegramUser, Payment, Credential, Server

admin.site.register(TelegramUser)
admin.site.register(Payment)
admin.site.register(Credential)
admin.site.register(Server)
