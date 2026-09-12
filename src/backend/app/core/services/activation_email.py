from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate

class ActivationEmail(EmailTemplate):
    template_name = "activation.html"
    template_name_plain = "activation.txt"
    subject = "Activate your account"

async def send_activation_email(email: str, token: str) -> None:
    activation_url = f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/activate/{token}"
    
    context = {
        "activation_url": activation_url,
        "expiry_time": settings.activation_token_expiration_minutes,
        "site_name": settings.site_name,
        "support_email": settings.support_email
    }
    
    await ActivationEmail.send_email(email_to=email, context=context)