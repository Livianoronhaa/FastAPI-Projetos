from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .. import schemas
from ..repositorie import crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from ..config import templates

router = APIRouter()

@router.get("/projetos", response_class=HTMLResponse)
async def projetos(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        projetos = crud.get_projetos(db, usuario_id=user.id)

        projetos_com_tarefas = []
        for projeto in projetos:
            tarefas = crud.get_tarefas_por_projeto(db, projeto_id=projeto.id)
            projetos_com_tarefas.append({
                "projeto": projeto,
                "tarefas": tarefas
            })

        return templates.TemplateResponse(
            "projetos.html",
            {"request": request, "user": user, "projetos_com_tarefas": projetos_com_tarefas, "show_nav": True}
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/criar-projeto", response_class=HTMLResponse)
async def exibir_formulario_criar_projeto(request: Request):
    return templates.TemplateResponse("criar_projeto.html", {"request": request})

@router.post("/criar-projeto", response_class=RedirectResponse)
async def criar_projeto(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    db: Session = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        novo_projeto = schemas.ProjetoCreate(
            nome=nome,
            descricao=descricao,
            usuario_id=user.id 
        )
        crud.create_projeto(db, novo_projeto)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.delete("/projetos/{projeto_id}/excluir", response_model=schemas.Mensagem)
def excluir_projeto(projeto_id: int, db: Session = Depends(get_db)):
    sucesso = crud.excluir_projeto(db, projeto_id=projeto_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return {"mensagem": "Projeto excluído com sucesso"}

@router.post("/projetos/{projeto_id}/editar", response_class=RedirectResponse)
async def editar_projeto(
    request: Request,
    projeto_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    db: Session = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        projeto_atualizado = schemas.ProjetoUpdate(nome=nome, descricao=descricao)
        crud.editar_projeto(db, projeto_id=projeto_id, projeto=projeto_atualizado)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_projeto(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    projeto = crud.get_projeto(db, projeto_id=projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return templates.TemplateResponse("editar_projeto.html", {"request": request, "projeto": projeto})