from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import SignUpRequest, SignInRequest, ChangePasswordRequest, AuthResponse, ConfirmSignUpRequest, ResendCodeRequest, ProfileResponse
from controllers.auth_controller import signup, signin, change_password, confirm_signup, resend_code, get_profile, signout

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/signup", response_model=AuthResponse)
async def signup_route(request: SignUpRequest):
    return signup(request.email, request.password)

@router.post("/confirm", response_model=AuthResponse)
async def confirm_signup_route(request: ConfirmSignUpRequest):
    return confirm_signup(request.email, request.code)

@router.post("/signin", response_model=AuthResponse)
async def signin_route(request: SignInRequest):
    return signin(request.email, request.password)

@router.post("/confirm", response_model=AuthResponse)
async def confirm_route(request: ConfirmSignUpRequest):
    return confirm_signup(request.email, request.code)

@router.post("/resend-code", response_model=AuthResponse)
async def resend_code_route(request: ResendCodeRequest):
    return resend_code(request.email)

@router.post("/change-password", response_model=AuthResponse)
async def change_password_route(request: ChangePasswordRequest):
    return change_password(request.access_token, request.old_password, request.new_password)

@router.get("/profile", response_model=ProfileResponse)
async def get_profile_route(credentials: HTTPAuthorizationCredentials = Security(security)):
    return get_profile(credentials.credentials)

@router.post("/signout", response_model=AuthResponse)
async def signout_route(credentials: HTTPAuthorizationCredentials = Security(security)):
    return signout(credentials.credentials)
