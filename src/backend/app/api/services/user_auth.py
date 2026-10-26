# The Single Responsibility Principle (SRP) states that a class, module, or function should have one, and only one, reason to change.

# In simpler terms: it should do exactly one thing.

# When a class takes on multiple responsibilities (e.g., a user service that handles database queries, sends welcome emails, and generates authentication tokens), a change to the email system might accidentally break the database logic. By splitting these into separate, single-purpose classes, your code becomes easier to test, maintain, and scale.


import asyncio
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.auth.models import User
from backend.app.auth.schema import AccountStatusSchema, UserCreateSchema
from backend.app.auth.utils import (
    generate_password_hash,
    generate_username,
    verify_password,
    create_activation_token,
    generate_otp
)
from backend.app.core.services.activation_email import send_activation_email
from backend.app.core.services.login_otp import send_login_otp_email
from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger()

class UserAuthService:
    async def get_user_by_email(
        self, email: str, session: AsyncSession, include_inactive: bool = False
    ) -> User | None:
        statement = select(User).where(User.email == email)
        
        if not include_inactive:
            statement = statement.where(User.is_active)
            
        result = await session.exec(statement)
        user = result.first()
        return user

    async def get_user_by_id_number(
        self, id_number: int, session: AsyncSession, include_inactive: bool = False
    ) -> User | None:
        statement = select(User).where(User.id_number == id_number)
        
        if not include_inactive:
            statement = statement.where(User.is_active)
            
        result = await session.exec(statement)
        user = result.first()
        return user

    
    async def get_user_by_id(
        self, 
        id: uuid.UUID, 
        session: AsyncSession, 
        include_inactive: bool = False
    ) -> User | None:
        statement = select(User).where(User.id == id)
        if not include_inactive:
            statement = statement.where(User.is_active)
        result = await session.exec(statement)
        user = result.first()
        return user

    async def check_user_email_exists(
        self, 
        email: str, 
        session: AsyncSession
    ) -> bool:
        user = await self.get_user_by_email(email, session, include_inactive=True)
        return bool(user)

    async def check_user_id_number_exists(
        self, 
        id_number: int, 
        session: AsyncSession
    ) -> bool:
        user = await self.get_user_by_id_number(id_number, session, include_inactive=True)
        return bool(user)

    async def verify_user_password(
        self, 
        plain_password: str, 
        hashed_password: str
    ) -> bool:
        return verify_password(plain_password, hashed_password)

    async def reset_user_state(
        self,
        user: User,
        session: AsyncSession,*,
        clear_otp: bool = True,
        log_action: bool = True
    ) -> None:
        previous_status = user.account_status
        user.failed_login_attempts = 0
        user.last_failed_login = None

        if clear_otp:
            user.otp = ""
            user.otp_expiry_time = None

        if user.account_status == AccountStatusSchema.LOCKED:
            user.account_status = AccountStatusSchema.ACTIVE if user.is_active else AccountStatusSchema.PENDING

        await session.commit()
        await session.refresh(user)

        if log_action and previous_status != user.account_status:
            logger.info(f"User {user.email} state reset: {previous_status} ->  {user.account_status}")

    async def validate_user_status(self, user: User) -> None:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "your account is not activated",
                    "action": "please activate your account first"
                }
            )
        if user.account_status == AccountStatusSchema.LOCKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "your account is locked",
                    "action": "please contact support"
                }
            )

        if user.account_status == AccountStatusSchema.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "your account is inactive",
                    "action": "please activate your account"
                }
            )
    async def generate_and_save_otp(self, user: User, session: AsyncSession) -> tuple[bool, str]:
        try:
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry_time = datetime.now(timezone.utc) + timedelta(
                minutes=settings.OTP_EXPIRATION_MINUTES
            )
            await session.commit()
            await session.refresh(user)

            for attempt in range(3):
                try:
                    await send_login_otp_email(user.email, otp)
                    logger.info(f"OTP sent to {user.email} successfully")
                    return True, otp
                except Exception as e:
                    logger.error(
                        f"Failed to send OTP email (attempt {attempt+1}): {e}"
                    )
                    if attempt == 2:
                        user.otp = ""
                        user.otp_expiry_time = None
                        try:
                            await session.commit()
                            await session.refresh(user)
                        except Exception as commit_exc:
                            logger.error(f"Failed to clear OTP after email dispatch failure: {commit_exc}")
                            await session.rollback()
                        return False, "Failed to dispatch OTP email"
                    await asyncio.sleep(0.5 * (attempt + 1))

            return False, "Failed to dispatch OTP email"
        except Exception as e:
            logger.error(f"Failed to generate and save OTP: {e}")
            try:
                await session.rollback()
            except Exception as rollback_exc:
                logger.error(f"Database rollback failed: {rollback_exc}")
            return False, str(e)

    async def create_user(
        self, 
        user_data: UserCreateSchema, 
        session: AsyncSession
    ) -> User: 
        user_data_dict = user_data.model_dump( 
            exclude={
                "confirm_password",
                "username", 
                "is_active", 
                "account_status"
            } 
        )

        password = user_data_dict.pop("password")

        new_user = User(
            username=generate_username(),
            hashed_password=generate_password_hash(password),
            is_active=False,
            account_status=AccountStatusSchema.PENDING,
            **user_data_dict
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        try:
            activation_token = create_activation_token(new_user.id)
            await send_activation_email(new_user.email, activation_token)
            logger.info(f"Activation email sent to {new_user.email}")
        except Exception as e:
            logger.error(
                f"User {new_user.email} created successfully, but failed to send activation email: {e}"
            )

        return new_user
    


    async def activate_user_account(
            self,
            token: str,
            session: AsyncSession
    ) -> User:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != "activation":
                raise ValueError("Invalid token type")

            user_id = uuid.UUID(payload["id"])


            user = await self.get_user_by_id(user_id, session, include_inactive=True)

            if not user: 
                raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, 
                                    detail={"status": "error", "message": "user not found"}, )

            if user.is_active:
                raise ValueError("user already activated")
            
            await self.reset_user_state(user, session, clear_otp=True)

            user.is_active = True
            user.account_status = AccountStatusSchema.ACTIVE

            await session.commit()
            await session.refresh(user)

            return user

        except jwt.ExpiredSignatureError:
            raise ValueError("activation token expired")
        except jwt.InvalidTokenError:
            raise ValueError("invalid activation token")
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(f"Failed to activate user account: {e}")
            raise e
    async def verify_login_otp( 
            self, 
            email: str, 
            otp: str, 
            session: AsyncSession 
            ) -> User: 
                try: 
                    user = await self.get_user_by_email(email, session) 
                    if not user: 
                        raise HTTPException( 
                            status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail={"status": "error", "message": "invalid credentials"} 
                        
                        )
                    await self.validate_user_status(user) 
                    await self.check_user_lockout(user, session) 
                    if not user.otp or user.otp != otp: 
                        await self.increment_failed_login_attempts(user, session) 
                        raise HTTPException( 
                            status_code=status.HTTP_400_BAD_REQUEST, 
                            detail={ "status": "error", "message": "invalid OTP", "action": "please check your OTP and try again" }
                             
                              )
                    if user.otp_expiry_time is None or user.otp_expiry_time < datetime.now(timezone.utc): 
                        raise HTTPException( status_code=status.HTTP_400_BAD_REQUEST, 
                                            detail={ "status": "error", "message": "OTP has expired", "action": "please request a new OTP" } 
                                        ) 
                    await self.reset_user_state(user, session, clear_otp=False) 
                    return user
                except HTTPException as http_exc: 
                    raise http_exc 
                except Exception as e: 
                    logger.error(f"Error during OTP verification: {e}") 
                    raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                                        detail={ "status": "error", "message": "failed to verify OTP", "action": "please try again later" } 
                                    )

                
    async def check_user_lockout( 
            self, 
            user:  User, 
            session: AsyncSession ) -> None: 
            if user.account_status != AccountStatusSchema.LOCKED: return 
            if user.last_failed_login is None: 
                return 
            lockout_time = user.last_failed_login + timedelta( minutes=settings.LOCKOUT_DURATION_MINUTES ) 
            current_time = datetime.now(timezone.utc) 
            
            if current_time >= lockout_time: 
                await self.reset_user_state(user, session, clear_otp=False) 
                logger.info(f"Lockout period ended for user {user.email}") 
                return 
            remaining_minutes = int((lockout_time - current_time).total_seconds() / 60) 
            logger.warning(f"Attempted login to locked account {user.email}") 
            
            raise HTTPException( 
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail={ "status": "error", 
                        "message": "your account is temporarily locked", 
                        "action": f"please try again after {remaining_minutes} minutes", 
                        "lockout_remaining_duration": remaining_minutes } 
                )


    async def increment_failed_login_attempts( 
            self, 
            user: User, 
            session: AsyncSession ) -> None: 
        # Increment the failed login attempt counter 
        user.failed_login_attempts += 1 
        # Record the timestamp of the failed attempt in UTC 
        user.last_failed_login = datetime.now(timezone.utc) 
        # Check if failed attempts reach or exceed the maximum allowed threshold 
        if user.failed_login_attempts >= settings.LOGIN_ATTEMPTS: user.account_status = AccountStatusSchema.LOCKED 
        logger.warning( f"User {user.email} has been locked out due to too many failed login attempts" ) 
        # Commit and refresh the database session 
        await session.commit() 
        await session.refresh(user) 
        # Instantiate the UserAuthService at the end of the module 

user_auth_service = UserAuthService()



        





        

    

