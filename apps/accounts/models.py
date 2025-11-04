from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Invitation(models.Model):
    ROLE_CHOICES = [("admin","admin"),("manager","manager"),("staff","staff")]
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    invited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_invitations")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def status(self) -> str:
        if self.revoked_at:
            return "revoked"
        if self.used_at:
            return "accepted"
        if self.expires_at and self.expires_at < timezone.now():
            return "expired"
        return "pending"

    def is_active(self) -> bool:

        if self.revoked_at or self.used_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])