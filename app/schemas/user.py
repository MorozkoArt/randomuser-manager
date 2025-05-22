from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    gender: str
    first_name: str
    last_name: str
    email: str
    phone: str

class UserCreate(UserBase):
    location: str
    picture_url: str

class User(UserBase):
    id: int
    location: str
    picture_url: str
    model_config = ConfigDict(from_attributes=True)