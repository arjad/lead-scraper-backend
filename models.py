from typing import List, Optional, Any
from pydantic import BaseModel

class UrlList(BaseModel):
    urls: List[str]
    proxy: Optional[str] = None

class ScrapeResult(BaseModel):
    url: str
    business_name: Optional[str] = None
    emails: List[str] = []
    phones: List[str] = []
    addresses: List[str] = []
    instagram: List[str] = []
    facebook: List[str] = []
    twitter: List[str] = []

class Lead(BaseModel):
    name: Optional[str] = ""
    rating: Optional[str] = ""
    reviews: Optional[str] = ""
    category: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    website: Optional[str] = ""
    email: Optional[str] = ""
    status: Optional[str] = ""
    # Fields to store augmented data
    facebook: Optional[str] = ""
    instagram: Optional[str] = ""
    twitter: Optional[str] = ""
    error: Optional[str] = ""

class LeadBatch(BaseModel):
    leads: List[Lead]
    proxy: Optional[str] = None

class JobStartResponse(BaseModel):
    job_id: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_leads: int
    completed_leads: int
    results: Optional[List[Lead]] = None
    error: Optional[str] = None

class SignUpRequest(BaseModel):
    email: str
    password: str

class ConfirmSignUpRequest(BaseModel):
    email: str
    code: str

class ResendCodeRequest(BaseModel):
    email: str

class SignInRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    access_token: str
    old_password: str
    new_password: str

class AuthResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None

class ProfileRequest(BaseModel):
    access_token: str

class ProfileResponse(BaseModel):
    username: str
    email: Optional[str] = None
