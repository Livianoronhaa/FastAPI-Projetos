from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .. import schemas
from ..repositorie import crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM, verify_password, create_access_token
from jose import JWTError, jwt
from ..config import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=RedirectResponse)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_usuario_by_email(db, email=email)
    if not user or not verify_password(password, user.senha_hash):
        raise HTTPException(status_code=400, detail="Email ou senha incorretos")

    access_token = create_access_token(data={"sub": user.email})

    response = RedirectResponse(url="/projetos", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout", response_class=RedirectResponse)
@router.post("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=RedirectResponse)
async def register(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario_by_email(db, email=email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    novo_usuario = schemas.UsuarioCreate(nome=nome, email=email, senha=senha)
    crud.create_usuario(db, novo_usuario)

    return RedirectResponse(url="/", status_code=303)