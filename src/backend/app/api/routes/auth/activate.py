from fastapi import APIRouter, Depends, HTTPException, status 
from sqlmodel.ext.asyncio.session import AsyncSession 
from backend.app.core.db import get_session 
from backend.app.core.logging import get_logger 
from backend.app.auth.schema import AccountStatusSchema, EmailRequestSchema 
from backend.app.api.services.user_auth import user_auth_service 
from backend.app.core.config import settings 
from backend.app.auth.utils import create_activation_token 
from backend.app.core.services.activation_email import send_activation_email


logger = get_logger()

router = APIRouter(prefix="/auth")

@router.get("/activate/{token}", status_code=status.HTTP_200_OK)

async def activate_user(
  token: str,
  session: AsyncSession = Depends(get_session)
):
  try:
    user = await user_auth_service.activate_user_account(token, session)

    return {"message": "Account activated successfully", "email": user.email}
  except ValueError as e:
    error_message = str(e)
    if error_message == "activation token expired":
      raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
          "status": "error",
          "message": "activation link has expired",
          "action": "please request a new activation link",
          "action_url": f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/resend-activation-link",
          "email_required": True,
        },
      )
    elif error_message == "invalid activation token":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          "status": "error",
          "message": "invalid activation token",
          "action": "please confirm that the link you clicked on is correct",
        },
      )
    elif error_message == "user already activated":
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
          "status": "error",
          "message": "user already activated",
          "action": "please login to your account",
        },
      )
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail={
        "status": "error",
        "message": error_message,
        "action": "please check the activation link and try again",
      },
    )
  except HTTPException as http_exception:
    raise http_exception
  except Exception as e:
    logger.error(f"failed to activate user account: {e}")
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail={
        "status": "error",
        "message": "failed to activate user account",
        "action": "please try again later",
      },
    )

@router.post("/resend-activation-link", status_code=status.HTTP_200_OK)
# @router.post("/resend-activation-link") 
async def resend_activation_link( email_data: EmailRequestSchema, session: AsyncSession = Depends(get_session) ): 

  # **Payload Validation**: The endpoint expects `email_data` formatted strictly against the `EmailRequestSchema` (which validates that the input is a properly formatted email string via Pydantic)
  # **Dependency Injection**: Injects the asynchronous database session (`AsyncSession`) using FastAPI's `Depends(get_session)`
  try: 
    # 1\. Fetch user by email (including inactive users) 
    user = await user_auth_service.get_user_by_email( email_data.email, session, include_inactive=True ) 

  #  **Explicit Inactive Inclusion**: Calls `get_user_by_email` with `include_inactive=True` . This flag is required because newly registered accounts awaiting activation have `is_active=False` . If `include_inactive` were `False`, the lookup would filter out pending users and fail to locate their records 
    

    # 2\. Handle non-existent users 
    if not user: raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail={ "status": "error", "message": "If an account exists with this email, please check your inbox for the activation link" } ) 

    # **Email Enumeration Prevention**: Even when returning an `HTTP 404 NOT FOUND` exception, the error message uses neutral language (`"If an account exists with this email..."`) . This prevents malicious actors from probing the API to discover registered email addresses


    # 3\. Prevent resending link if user account is already active 
    if user.is_active or user.account_status == AccountStatusSchema.ACTIVE: raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail={ "status": "error", "message": "user account already activated", "action": "please login to your account" } ) 

    #**Duplicate Prevention**: Checks if `user.is_active` is already `True` or if `account_status` is `ACTIVE` [cite: 334, 335]. If the user is already verified, it halts execution and returns an `HTTP 400 Bad Request` directing them to the login endpoint instead


    # 4\. Generate a new activation token and send email 
    activation_token = create_activation_token(user.id) 
    await send_activation_email(user.email, activation_token) 

    # **Fresh JWT Issuance**: Calls `create_activation_token(user.id)` to produce a signed JWT with a renewed expiration timestamp .
    #  **Asynchronous Email Task**: Passes `user.email` and the new JWT token into `send_activation_email`, which queues a Celery task to dispatch the email via FastMail


    return { "message": "If an account exists with this email, please check your inbox for the activation link" } 

  # **Response Payload**: Returns a generic success dictionary confirming the request was processed



  except HTTPException as http_exception: raise http_exception 
  except Exception as e: logger.error(f"failed to resend activation link: {e}") 
  raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={ "status": "error", "message": "failed to resend activation link", "action": "please try again later or contact support if the issue persists" } )

  # **Exception Handling**:
    #  Explicit `HTTPException` instances are caught and re-raised directly [cite: 352, 353].
    #  Unexpected system failures are logged via `logger.error(...)` and return an **HTTP 500 Internal Server Error** with a structured error detail dictionary

