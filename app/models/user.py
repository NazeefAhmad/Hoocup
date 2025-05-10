from pydantic import BaseModel
from typing import List, Optional

class Preferences(BaseModel):
    loves: List[str]
    dislikes: List[str]
    interests: List[str]

class User(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    age: Optional[int] = None
    gender_pref: Optional[str] = None
    # preferences: Preferences
