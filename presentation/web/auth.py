from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from domain.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    new_password: str

@router.post("/register")
async def register(data: RegisterRequest):
    result = AuthService.register(data.email, data.password, data.full_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.post("/login")
async def login(data: LoginRequest):
    result = AuthService.login(data.email, data.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@router.post("/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не предоставлен")
    token = auth_header.split(" ")[1]
    AuthService.logout(token)
    return {"success": True, "message": "Выход выполнен"}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    AuthService.reset_password(data.email)
    return {"success": True, "message": "Ссылка для сброса пароля отправлена на email"}

@router.post("/update-password")
async def update_password(request: Request, data: UpdatePasswordRequest):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не предоставлен")
    token = auth_header.split(" ")[1]
    result = AuthService.update_password(token, data.new_password)
    if not result:
        raise HTTPException(status_code=400, detail="Ошибка смены пароля")
    return {"success": True, "message": "Пароль изменён"}

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="presentation/web/templates")

@router.get("/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register-page", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.get("/reset-password-page", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return templates.TemplateResponse("auth/reset_password.html", {"request": request})