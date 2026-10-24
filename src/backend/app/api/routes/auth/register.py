from fastapi import APIRouter, Depends, HTTPException, status 
from sqlmodel.ext.asyncio.session import AsyncSession 
from backend.app.core.db import get_session 
from backend.app.core.logging import get_logger 
from backend.app.auth.schema import UserCreateSchema, UserRead 
from backend.app.api.services.user_auth import user_auth_service 

logger = get_logger() 
router = APIRouter(prefix="/auth", tags=["Authentication"]) 

# user_auth_service = UserAuthService() 
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED) 

async def register_user( user_data: UserCreateSchema, session: AsyncSession = Depends(get_session) ): 
  
  try: 
    # Check if email is already registered 
    if await user_auth_service.check_user_email_exists(user_data.email, session): raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists") 
    # Check if ID number is already registered 
    if await user_auth_service.check_user_id_number_exists(user_data.id_number, session): raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, detail="User with this ID number already exists" ) 
    # Create the new user record and send activation email 
    new_user = await user_auth_service.create_user(user_data, session) 
    logger.info(f"New user {new_user.email} registered successfully. Awaiting activation.") 
    return new_user 
  except HTTPException as http_exc: 
    await session.rollback() 
    raise http_exc 
  except Exception as e: 
    await session.rollback() 
    logger.error(f"Failed to register user: {e}") 
    raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


