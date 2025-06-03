from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone_number", "link_precedence", "linked_id", "created_at", "updated_at", "deleted_at")
    list_filter = ("link_precedence",)
    search_fields = ("email", "phone_number")
