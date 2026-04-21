from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)


class RegisterResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class MeSerializer(UserSerializer):
    is_staff = serializers.BooleanField()
    totp_enabled = serializers.BooleanField()
    avatar_url = serializers.CharField(allow_null=True)


class LoginResponseSerializer(UserSerializer):
    access = serializers.CharField()


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)


class LoginErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
    code = serializers.CharField(required=False)


class TotpSetupSerializer(serializers.Serializer):
    secret = serializers.CharField()
    qr_code = serializers.CharField()


class TotpCodeSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


class TotpDisableSerializer(serializers.Serializer):
    password = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class TwoFactorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(min_length=6, max_length=6)


class TwoFactorRequiredSerializer(serializers.Serializer):
    requires_2fa = serializers.BooleanField()
    detail = serializers.CharField()


class AvatarSerializer(serializers.Serializer):
    avatar_url = serializers.CharField(allow_null=True)
