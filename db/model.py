from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LinkedinPost(BaseModel):
    post_urn: str
    author_urn: str
    author_name: str
    author_title: str
    author_profile_url: str
    post_text: str
    post_type: str  # "text", "url", or "image"
    created_at: datetime
    # Optional field for image posts
    image_url: Optional[str] = None
    
    # Optional fields for URL posts
    url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    

    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }