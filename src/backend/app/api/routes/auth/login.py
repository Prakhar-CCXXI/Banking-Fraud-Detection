from fastapi import APIRouter, Depends, HTTPException, status, Response 
from sqlmodel.ext.asyncio.session import AsyncSession 
from backend.app.core.db import get_session 
from backend.app.core.logging import get_logger 
from backend.app.auth.utils import set_auth_cookies, create_jwt_token 
from backend.app.core.config import settings 
from backend.app.auth.schema import LoginRequestSchema, OTPVerifyRequestSchema 
from backend.app.api.services.user_auth import user_auth_service 

logger = get_logger() 
router = APIRouter(prefix="/auth") 


@router.post("/login/request-otp", status_code=status.HTTP_200_OK) 
async def request_login_otp(
    login_data: LoginRequestSchema,
    session: AsyncSession = Depends(get_session)
):
    """
    Initiates the login flow by verifying credentials and dispatching a one-time password (OTP).
    Returns a generic message to prevent account enumeration attacks.
    """
    try: 
        # Retrieve user record by email, including inactive accounts to ensure appropriate validation
        user = await user_auth_service.get_user_by_email(login_data.email, session, include_inactive=True) 
        
        if user:
            # Check whether the account is currently locked due to too many failed attempts
            await user_auth_service.check_user_lockout(user, session) 
            
            # Verify the submitted plain-text password against the hashed password in DB
            if not await user_auth_service.verify_user_password(login_data.password, user.hashed_password):
                await user_auth_service.increment_failed_login_attempts(user, session) 
                remaining_attempts = settings.LOGIN_ATTEMPTS - user.failed_login_attempts 
                
                if remaining_attempts > 0:
                    error_message = (
                        f"Invalid credentials. You have {remaining_attempts} "
                        f"attempt{'s' if remaining_attempts != 1 else ''} remaining before "
                        "your account is temporarily locked"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "status": "error",
                            "message": error_message,
                            "action": "please check your email and password and try again",
                            "remaining_attempts": remaining_attempts
                        }
                    )
                else:
                    error_message = (
                        f"Invalid credentials. Your account has been temporarily locked due to too many failed attempts. "
                        f"Please try again after {settings.LOCKOUT_DURATION_MINUTES} minutes"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "status": "error",
                            "message": error_message,
                            "action": "please check your email and password and try again",
                            "remaining_attempts": remaining_attempts
                        }
                    )

            # Ensure the user account has been activated before issuing a login OTP
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "your account is not activated",
                        "action": "please activate your account first"
                    }
                )

            # Reset failed login attempts upon successful password verification
            await user_auth_service.reset_user_state(
                user, session, clear_otp=True, log_action=True
            )

            # Generate OTP, persist to database, and dispatch email via background worker
            success, error_msg = await user_auth_service.generate_and_save_otp(user, session)
            if not success:
                logger.error(f"Failed to generate and dispatch OTP for {user.email}: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "message": "Failed to send login OTP. Please try again later.",
                        "action": "please try again later"
                    }
                )

        # Generic response to prevent email enumeration attacks
        return {
            "message": "If an account exists with this email, an OTP has been sent to it"
        }

    except HTTPException as http_exception:
        # Re-raise explicit HTTP exceptions directly
        raise http_exception
    except Exception as e:
        logger.error(f"Failed to process login OTP request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "failed to process login OTP request",
                "action": "please try again later"
            }
        )


@router.post("/login/verify-otp", status_code=status.HTTP_200_OK) 
async def verify_login_otp(
    verify_data: OTPVerifyRequestSchema,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    """
    Verifies user OTP, issues authentication tokens, and sets secure auth cookies.
    """
    try: 
        user = await user_auth_service.verify_login_otp(
            verify_data.email, verify_data.otp, session
        )
        await user_auth_service.reset_user_state(
            user, session, clear_otp=True, log_action=True
        )
        access_token = create_jwt_token(user.id)
        refresh_token = create_jwt_token(user.id, type=settings.COOKIE_REFRESH_NAME)
        set_auth_cookies(response, access_token, refresh_token)

        return {
            "message": "login successful",
            "user": {
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "id_number": user.id_number,
                "role": user.user_role.value if hasattr(user.user_role, "value") else user.user_role
            }
        }
    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Failed to verify login OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "failed to verify OTP",
                "action": "please try again later"
            }
        )
