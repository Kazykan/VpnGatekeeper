from rest_framework import serializers
from .models import TelegramUser, Payment, Credential, Server


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credential
        fields = "__all__"


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = "__all__"
