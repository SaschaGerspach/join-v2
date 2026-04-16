from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from config.serializers import DetailSerializer
from .models import Contact
from .serializers import (
    ContactCreateSerializer,
    ContactSerializer,
    ContactUpdateSerializer,
)


class _ContactPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


def serialize_contact(contact):
    return {
        "id": contact.pk,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone": contact.phone,
    }


@extend_schema(
    methods=["GET"],
    responses={200: ContactSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=ContactCreateSerializer,
    responses={201: ContactSerializer, 400: DetailSerializer},
)
@api_view(["GET", "POST"])
def contact_list(request):
    if request.method == "GET":
        contacts = request.user.contacts.all().order_by("last_name", "first_name")
        paginator = _ContactPagination()
        page = paginator.paginate_queryset(contacts, request)
        return paginator.get_paginated_response([serialize_contact(c) for c in page])

    required = ["first_name", "last_name", "email"]
    for field in required:
        if not request.data.get(field, "").strip():
            return Response({"detail": f"{field} is required."}, status=status.HTTP_400_BAD_REQUEST)

    contact = Contact.objects.create(
        owner=request.user,
        first_name=request.data["first_name"].strip(),
        last_name=request.data["last_name"].strip(),
        email=request.data["email"].strip().lower(),
        phone=request.data.get("phone", "").strip(),
    )
    return Response(serialize_contact(contact), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=ContactUpdateSerializer,
    responses={200: ContactSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def contact_detail(request, pk):
    try:
        contact = Contact.objects.get(pk=pk, owner=request.user)
    except Contact.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        for field in ["first_name", "last_name", "email", "phone"]:
            if field in request.data:
                value = request.data[field].strip()
                if field == "email":
                    value = value.lower()
                setattr(contact, field, value)
        contact.save()
        return Response(serialize_contact(contact))

    contact.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
