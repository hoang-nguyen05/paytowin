from django.conf import settings
from django.db import models


class Badge(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="holders")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "badge")]

    def __str__(self) -> str:
        return f"{self.user_id} {self.badge.code}"