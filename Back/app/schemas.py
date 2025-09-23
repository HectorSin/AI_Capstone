from pydantic import BaseModel, EmailStr
from typing import List, Optional

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    nickname: str

class UserCreate(UserBase):
    social_id: str
    provider: str

class User(UserBase):
    user_id: int
    plan: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

# --- AnalysisTopic Schemas ---
class AnalysisTopicBase(BaseModel):
    title: str
    one_line_summary: Optional[str] = None
    thumbnail_url: Optional[str] = None

class AnalysisTopicCreate(AnalysisTopicBase):
    pass

class AnalysisTopic(AnalysisTopicBase):
    topic_id: int
    user_id: int
    
    class Config:
        from_attributes = True