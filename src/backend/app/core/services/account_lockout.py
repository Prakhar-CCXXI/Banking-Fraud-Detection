from datetime import datetime, timedelta # Imports datetime and timedelta for date operations and calculating time differences  
from backend.app.core.config import settings # Imports application configuration settings for lockout parameters and site details  
from backend.app.core.emails.base import EmailTemplate # Imports EmailTemplate base class to enable Jinja email rendering and task dispatching 

class AccountLockoutEmail(EmailTemplate): # Subclasses EmailTemplate to define the account lockout email configuration  
  template_name = "account_lockout.html" # Sets the Jinja HTML email template filename   
  template_name_plain = "account_lockout.txt" # Sets the Jinja plain-text fallback email template filename 
  subject = "account security alert" # Sets the subject line for the account lockout email 

# Defines asynchronous service function to format context and send lockout email 
async def send_account_lockout_email(email: str, lockout_time: datetime) -> None:
    # Recipient email address string parameter
    # Datetime parameter representing when the account was locked out    
    # Specifies function returns None as it asynchronously queues background tasks  
         
    unlock_time = lockout_time + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)

    context = { # Initializes context dictionary containing dynamic variables for Jinja template rendering 
        "lockout_duration": settings.LOCKOUT_DURATION_MINUTES, # Passes lockout duration in minutes to template context 
        "lockout_time": lockout_time.strftime("%Y-%m-%d %H:%M:%S"), # Formats lockout timestamp string in YYYY-MM-DD HH:MM:SS format  
        "unlock_time": unlock_time.strftime("%Y-%m-%d %H:%M:%S"), # Formats unlock timestamp string in YYYY-MM-DD HH:MM:SS format  
        "site_name": settings.SITE_NAME, # Passes site name setting to template context  
        "support_email": settings.SUPPORT_EMAIL # Passes support email address setting to template context  
    } 
    await AccountLockoutEmail.send_email( 
        # Calls inherited send_email class method to asynchronously queue Celery email task  
        email_to=email, # Passes recipient email address 
        context=context # Passes populated context dictionary  
    ) 
      