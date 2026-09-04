from enum import Enum
from sqlmodel import SQLModel, Field
from pydantic import EmailStr,field_validator
from fastapi import HTTPException, status

class SecurityQuestionsSchema():
  MOTHER_MAIDEN_NAME = "mother_maiden_name"
  CHILDHOOD_FRIEND = "childhood_friend"
  FAVOURITE_COLOR = "favorite_color"
  BIRTH_CITY = "birth_city"

  @classmethod
  def get_description(cls,value:"SecurityQuestionsSchema") -> str:
    description = {
      cls.MOTHER_MAIDEN_NAME: "What is the name of your mother ?",
      cls.CHILDHOOD_FRIEND: "What is the name of your childhood friend ?",
      cls.FAVOURITE_COLOR: "What is your favorite color ?",
      cls.BIRTH_CITY: "What is the name of the city you were born in ?"
    }

    return description.get(value, "Unknown security question")

class AccountStatusSchema(str, Enum):
  ACTIVE = "active"
  INACTIVE = "inactive" 
  LOCKED = "locked" 
  PENDING = "pending"

class RoleChoicesSchema(str,Enum):
  CUSTOMER = "customer"
  ACCOUNT_EXECUTIVE = "account_executive" 
  BRANCH_MANAGER = "branch_manager"
  ADMIN = "admin"
  SUPER_ADMIN = "super_admin"
  TELLER = "teller"

class BaseUserSchema(SQLModel):
    username: str | None = Field(default=None, max_length=12, unique=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(max_length=30)
    middle_name: str | None = Field(default=None, max_length=30)
    last_name: str = Field(max_length=30)
    id_number: int = Field(unique=True, ge=0)
    is_active: bool = False
    is_superuser: bool = False
    security_question: SecurityQuestionsSchema = Field(max_length=30)
    security_answer: str = Field(max_length=30)
    account_status: AccountStatusSchema = Field(default=AccountStatusSchema.INACTIVE)
    user_role: RoleChoicesSchema = Field(default=RoleChoicesSchema.CUSTOMER)

class UserCreateSchema(BaseUserSchema):
   
    password: str = Field(min_length=8, max_length=40)
    confirm_password: str = Field(min_length=8, max_length=40)

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str, values: Any) -> str:
       
        data = getattr(values, "data", values) if not isinstance(values, dict) else values
        
        if "password" in data and v != data["password"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Passwords do not match.",
                    "action": "Please ensure that the password you entered matches."
                }
            )
        return v