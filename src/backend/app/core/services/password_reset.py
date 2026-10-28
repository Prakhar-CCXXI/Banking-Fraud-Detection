import uuid # Imports uuid module for handling unique user identifier types  
from backend.app.core.config import settings # Imports application configuration settings for URLs and token expiration times 
from backend.app.core.emails.base import EmailTemplate # Imports base EmailTemplate class to handle Jinja rendering and Celery task queuing  
from backend.app.auth.utils import create_password_reset_token # Imports utility function to generate signed JWT password reset tokens 

class PasswordResetEmail(EmailTemplate): # Subclasses EmailTemplate to configure password reset email parameters 
  template_name = "password_reset.html" # Specifies HTML template filename for password reset emails 
  template_name_plain = "password_reset.txt" # Specifies plain-text fallback template filename  
  subject = "reset your password" # Sets subject line header for password reset emails 

async def send_password_reset_email( 
    # Defines asynchronous service function to format context and send password reset email 
    # Recipient email address parameter  
    # User's UUID identifier parameter
    email: str,
    user_id: uuid.UUID  ) -> None : 
    # Specifies function returns None as it asynchronously queues background tasks  
    reset_token = create_password_reset_token(user_id) # Generates signed JWT password reset token using user ID 

    reset_url = ( # Begins reset URL string formatting  
       f"{settings.API_BASE_URL}" # Injects API base URL setting into reset URL 
       f"{settings.API_V1_STR}" # Injects API version 1 route prefix setting into reset URL  
       f"/auth/reset-password/{reset_token}" # Appends auth reset-password path and generated JWT reset token  
      )

    context = { 
       # Initializes context dictionary containing dynamic variables for Jinja template rendering  
       "reset_url": reset_url, # Passes complete password reset URL string to template context 
       "expiry_time": settings.PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES, # Passes token expiration duration in minutes from settings to template context  
       "expire_time": settings.PASSWORD_RESET_TOKEN_EXPIRATION_MINUTES,
       "site_name": settings.SITE_NAME, # Passes site name configuration setting to template context 
       "support_email": settings.SUPPORT_EMAIL # Passes support email address configuration setting to template context 
      }

    await PasswordResetEmail.send_email( 
       # Calls inherited send_email class method to asynchronously queue Celery email task 
       email_to=email, # Passes recipient email address 
       context=context # Passes populated context dictionary 
      )
