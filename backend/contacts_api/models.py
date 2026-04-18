from django.conf import settings
from django.db import models


class Contact(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        unique_together = ("owner", "email")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
