from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.auth.schema import PasswordResetConfirmSchema, PasswordResetRequestSchema
from backend.app.core.db import get_session
from backend.app.api.services.user_auth import user_auth_service

from backend.app.core.services.password_reset import send_password_reset_email
from backend.app.core.logging import get_logger

logger = get_logger()

router = APIRouter(prefix="/auth")

@router.post("/request-password-reset", status_code=status.HTTP_200_OK) 
# Registers POST endpoint on '/auth/request-password-reset' returning HTTP 200 OK
async def request_password_reset( 
  # Defines asynchronous route handler for processing password reset requests  
  reset_data: PasswordResetRequestSchema,
  # Validates incoming request body containing user email against PasswordResetRequestSchema  
  session: AsyncSession = Depends(get_session) # Injects asynchronous database session dependency into route  
  ) -> dict: # Specifies function returns a dictionary response  
  
  try: # Begins main try block to capture and manage request processing exceptions  
    user = await user_auth_service.get_user_by_email( 
      # Queries database for user account matching submitted email address  
      reset_data.email, session, include_inactive=True # Passes email, database session, and includes inactive accounts in lookup  
      )   
    if user: # Checks if a user matching the provided email address exists in database  
      await send_password_reset_email(user.email, user.id) # Asynchronously triggers password reset email containing signed JWT token  
    return { # Returns generic JSON response payload to prevent email enumeration attacks  
      "message": "If an account exists with this email, you will receive password reset instructions shortly." 
      # Returns user message explaining instructions will be sent if account exists  
      } 
  except Exception as e: # Catches any unhandled system exceptions during reset request execution  
    logger.error(f"password reset request failed: {e}") # Logs unexpected error message and exception details 
    
    raise HTTPException( # Raises HTTP exception for unhandled server error  
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Sets status code to HTTP 500 Internal Server Error 
        detail={ # Opens structured error detail response dictionary  
          "status": "error", # Sets status field indicator to error 
          "message": "failed to process password reset request", # Informs client password reset request failed  
          "action": "please try again later" # Directs user to retry request later 
          }  
        )

@router.post("/reset-password/{token}", status_code=status.HTTP_200_OK) # Registers POST endpoint on '/auth/reset-password/{token}' returning HTTP 200 OK  
async def reset_password( # Defines asynchronous route handler for resetting password using URL token  
  token: str, # Receives JWT reset token parameter from URL path  
  reset_data: PasswordResetConfirmSchema, # Validates request body containing new_password and confirm_password fields 
  session: AsyncSession = Depends(get_session) # Injects asynchronous database session dependency into route 
) -> dict:   
  try: # Begins try block for password reset execution and error catching  
    await user_auth_service.reset_password( # Calls service method to decode token, verify user, hash new password, and update state  
      token, reset_data.new_password, session # Passes JWT reset token, validated new password string, and database session  
    )   
    return { # Returns JSON success response dictionary upon completion  
      "message": "password has been reset successfully" # Returns success status confirmation message  
      }

  except ValueError as e: # Catches token validation errors (e.g., expired or invalid reset token)  
    raise HTTPException( # Raises HTTP 400 Bad Request exception for invalid/expired tokens 
       status_code=status.HTTP_400_BAD_REQUEST, # Sets status code to HTTP 400 Bad Request  
      detail={ # Opens structured error detail dictionary 
        "status": "error", # Sets status field indicator to error 
        "message": str(e), # Returns specific validation error message (e.g. token expired) 
        "action": "please request a new password reset link" # Directs user to request a fresh password reset link 
        }  
      )
  except HTTPException:
    raise
  except Exception as e: # Catches unexpected server or database exceptions  
    logger.error(f"password reset failed: {e}") # Logs unexpected error message and exception details 
    raise HTTPException( # Raises HTTP 500 Internal Server Error exception 
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Sets status code to HTTP 500  
      detail={ # Opens structured error detail dictionary  
        "status": "error", # Sets status field indicator to error 
        "message": "Failed to reset password", # Sets descriptive error message 
        "action": "Please try again later" # Provides actionable guidance to user  
        }  
      )
