import random
import string
import uuid  # Standard library module for generating and manipulating universally unique identifiers (UUIDs) 
import jwt  # PyJWT library used for encoding and decoding JSON Web Tokens 
from datetime import datetime, timedelta, timezone  # Datetime utilities for timezone-aware timestamps and expiration math
from backend.app.core.config import settings
from fastapi import Response  # FastAPI Response object used to modify HTTP headers and attach/clear cookies 
from backend.app.core.config import settings  # Application configuration settings containing JWT and cookie settings 
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

def generate_otp(length: int = 6) -> str:
  otp = "".join(random.choices(string.digits, k = length))
  return otp

def generate_password_hash(password: str)-> str:
  return _ph.hash(password)

def verify_password(password: str, hashed_password: str)-> bool:
  try:
    return _ph.verify(hashed_password, password)
  except VerifyMismatchError:
    return False

def generate_username()->str:
  bank_name = settings.SITE_NAME
  words = bank_name.split()
  prefix = "".join([word[0] for word in words]).upper()
  remaining_length = 12 - len(prefix) -1
  random_string = "".join(random.choices(string.ascii_uppercase + string.digits, k = remaining_length))
  username = f"{prefix}-{random_string}"
  return username

def create_activation_token(id: uuid.UUID) -> str:
    payload = {
        "id": str(id),
        "type": "activation",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACTIVATION_TOKEN_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_jwt_token(id: uuid.UUID, type: str = settings.COOKIE_ACCESS_NAME) -> str:  # Generates signed JWT access or refresh token 
    if type == settings.COOKIE_ACCESS_NAME:
        expire_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRATION_MINUTES)
    else:
        expire_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRATION_DAYS)

    payload = {  # Initializes payload dictionary to encode inside the JWT 
        "id": str(id),  # Converts user UUID object to string for JSON serialization 
        "type": type,  # Denotes token type (access_token or refresh_token) 
        "exp": datetime.now(timezone.utc) + expire_delta,  # Sets UTC timestamp when token expires 
        "iat": datetime.now(timezone.utc)  # Records current UTC timestamp as token creation time 
    }  # Closes JWT payload dictionary 

    return jwt.encode(payload, settings.SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)  # Encodes and returns signed JWT string 

def set_auth_cookies(  # Attaches access, refresh, and logged_in cookies to response headers 
    response: Response,  # FastAPI Response instance being returned to client 
    access_token: str,  # Generated JWT access token string 
    refresh_token: str | None = None  # Optional generated JWT refresh token string 
) -> None:  # Returns None as it mutates response object in-place 
    cookie_settings = {  # Defines baseline security parameters shared by all authentication cookies 
        "path": settings.COOKIE_PATH,  # Path "/" making cookies active across all application endpoints 
        "secure": settings.COOKIE_SECURE,  # Enforces HTTPS delivery in production environments 
        "httponly": settings.COOKIE_HTTP_ONLY,  # Disables JavaScript access to protect tokens from XSS attacks 
        "samesite": settings.COOKIE_SAMESITE,  # Applies SameSite policy ("lax") to protect against CSRF attacks 
    }  # Closes base cookie settings dictionary 

    access_cookie_settings = cookie_settings.copy()  # Clones baseline configuration for access token cookie 
    access_cookie_settings["max_age"] = settings.JWT_ACCESS_TOKEN_EXPIRATION_MINUTES * 60  # Sets max age in seconds for access token 
    response.set_cookie(  # Attaches access token HTTP-only cookie to response 
        key=settings.COOKIE_ACCESS_NAME,  # Sets cookie key name ("access_token") 
        value=access_token,  # Assigns signed JWT access token string 
        **access_cookie_settings  # Unpacks access cookie settings dictionary 
    )  # Closes set_cookie call for access token 

    if refresh_token:  # Checks if refresh token was provided before attaching refresh cookie 
        refresh_cookie_settings = cookie_settings.copy()  # Clones baseline configuration for refresh token cookie 
        refresh_cookie_settings["max_age"] = (  # Begins max_age assignment calculation for refresh token 
            settings.JWT_REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 60 * 60  # Converts refresh token lifetime from days into seconds 
        )  # Closes max_age assignment calculation 
        response.set_cookie(  # Attaches refresh token HTTP-only cookie to response 
            key=settings.COOKIE_REFRESH_NAME,  # Sets cookie key name ("refresh_token") 
            value=refresh_token,  # Assigns signed JWT refresh token string 
            **refresh_cookie_settings  # Unpacks refresh cookie settings dictionary 
        )  # Closes set_cookie call for refresh token 

    logged_in_cookie_settings = cookie_settings.copy()  # Clones baseline configuration for frontend status cookie 
    logged_in_cookie_settings["httponly"] = False  # Overrides HTTP-only flag to allow frontend JavaScript to read login status 
    logged_in_cookie_settings["max_age"] = settings.JWT_ACCESS_TOKEN_EXPIRATION_MINUTES * 60  # Syncs max age with access token expiration 
    response.set_cookie(  # Attaches non-sensitive status cookie to response 
        key=settings.COOKIE_LOGGED_IN_NAME,  # Sets cookie key name ("logged_in") 
        value="true",  # Sets plain boolean indicator string 
        **logged_in_cookie_settings  # Unpacks status cookie settings dictionary 
    )  # Closes set_cookie call for logged_in status 

def delete_auth_cookies(response: Response) -> None:  # Clears all authentication cookies upon user logout [
    response.delete_cookie(key=settings.COOKIE_ACCESS_NAME)  # Commands browser to delete JWT access token cookie 
    response.delete_cookie(key=settings.COOKIE_REFRESH_NAME)  # Commands browser to delete JWT refresh token cookie 
    response.delete_cookie(key=settings.COOKIE_LOGGED_IN_NAME)  # Commands browser to delete frontend logged_in status cookie 






