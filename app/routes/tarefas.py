from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from .. import schemas
from ..repositorie import crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from ..config import templates

router = APIRouter()

@router.get("/criar-tarefa", response_class=HTMLResponse)
async def exibir_formulario_criar_tarefa(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse("criar_tarefa.html", {
        "request": request, 
        "projeto_id": projeto_id,
        "prioridades": ["baixa", "media", "alta"]
    })

@router.post("/criar-tarefa", response_class=RedirectResponse)
async def criar_tarefa(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    projeto_id: int = Form(...),
    prioridade: str = Form(...),
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

        nova_tarefa = schemas.TarefaCreate(
            nome=nome,
            descricao=descricao,
            projeto_id=projeto_id,
            prioridade=prioridade,
            usuario_id=user.id
        )
        crud.create_tarefa(db, nova_tarefa)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.post("/tarefas/{tarefa_id}/status", response_class=RedirectResponse)
async def atualizar_status_tarefa(
    request: Request,
    tarefa_id: int,
    status: bool = Form(...),
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

        # Verifica se o usuário tem permissão para alterar esta tarefa
        tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
        if not tarefa or tarefa.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Não autorizado")

        # Atualiza o status
        crud.atualizar_status_tarefa(db, tarefa_id=tarefa_id, status=status)

        # Redireciona de volta para a página de projetos
        return RedirectResponse(url="/projetos", status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
@router.get("/tarefas/{tarefa_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_tarefa(request: Request, tarefa_id: int, db: Session = Depends(get_db)):
    tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return templates.TemplateResponse("editar_tarefa.html", {"request": request, "tarefa": tarefa})

@router.post("/tarefas/{tarefa_id}/editar", response_class=RedirectResponse)
async def editar_tarefa(
    request: Request,
    tarefa_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    prioridade: str = Form(...),
    status: bool = Form(...),
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

        tarefa_atualizada = schemas.TarefaUpdate(nome=nome, descricao=descricao, status=status, prioridade=prioridade)
        crud.editar_tarefa(db, tarefa_id=tarefa_id, tarefa=tarefa_atualizada)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.delete("/tarefas/{tarefa_id}/excluir", response_model=schemas.Mensagem)
def excluir_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    sucesso = crud.excluir_tarefa(db, tarefa_id=tarefa_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa excluída com sucesso"}