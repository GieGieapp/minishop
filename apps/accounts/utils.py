from django.core.mail import send_mail
from django.conf import settings

def send_invitation_email(email: str, token: str):
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:3000")
    link = f"{base}/accept?token={token}"
    send_mail(
        subject="Invitation",
        message=f"Open this link to accept: {link}",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
        recipient_list=[email],
        fail_silently=False,
    )
