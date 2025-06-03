from django.db import models

class Contact(models.Model):
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    linked_id = models.IntegerField(null=True, blank=True)
    link_precedence = models.CharField(max_length=10, choices=[('primary', 'Primary'), ('secondary', 'Secondary')], default='primary')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.phone_number}"
