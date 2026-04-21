import base64
import io

import pyotp
import qrcode
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..serializers import TotpSetupSerializer, TotpCodeSerializer, TotpDisableSerializer


@extend_schema(responses={200: TotpSetupSerializer})
@api_view(["POST"])
def totp_setup(request):
    user = request.user
    if user.totp_enabled:
        return Response({"detail": "2FA is already enabled."}, status=status.HTTP_400_BAD_REQUEST)

    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.save(update_fields=["totp_secret"])

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="Join")

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return Response({
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
    })


@extend_schema(request=TotpCodeSerializer, responses={200: None})
@api_view(["POST"])
def totp_confirm(request):
    user = request.user
    if user.totp_enabled:
        return Response({"detail": "2FA is already enabled."}, status=status.HTTP_400_BAD_REQUEST)
    if not user.totp_secret:
        return Response({"detail": "Call setup first."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TotpCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    code = serializer.validated_data["code"]
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code):
        return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

    user.totp_enabled = True
    user.save(update_fields=["totp_enabled"])
    return Response({"detail": "2FA enabled."})


@extend_schema(request=TotpDisableSerializer, responses={200: None})
@api_view(["POST"])
def totp_disable(request):
    user = request.user
    if not user.totp_enabled:
        return Response({"detail": "2FA is not enabled."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = TotpDisableSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(serializer.validated_data["password"]):
        return Response({"detail": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)

    code = serializer.validated_data["code"]
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code):
        return Response({"detail": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

    user.totp_enabled = False
    user.totp_secret = ""
    user.save(update_fields=["totp_enabled", "totp_secret"])
    return Response({"detail": "2FA disabled."})
