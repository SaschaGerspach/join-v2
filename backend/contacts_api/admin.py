from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'owner')
    list_filter = ('owner',)
    search_fields = ('first_name', 'last_name', 'email', 'owner__email')
    raw_id_fields = ('owner',)
