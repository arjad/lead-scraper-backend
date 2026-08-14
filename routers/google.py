from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import controllers.google_controller as google_controller

router = APIRouter(prefix="/auth/google", tags=["Google"])

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    content: str

@router.get("/login")
def login_google():
    try:
        url = google_controller.get_auth_url()
        return RedirectResponse(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
def google_callback(code: str = None, error: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Error from Google: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
        
    try:
        google_controller.exchange_code(code)
        return {"message": "Successfully authenticated with Google. Credentials saved."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-email")
def send_email(request: EmailRequest):
    try:
        result = google_controller.send_email(request.to_email, request.subject, request.content)
        return {"message": "Email sent successfully", "id": result.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
