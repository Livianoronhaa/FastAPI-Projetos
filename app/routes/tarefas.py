from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm import Session
from .. import schemas, models
from ..repositorie import crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from ..config import templates

router = APIRouter()

def verificar_acesso_projeto(db: Session, user_id: int, projeto_id: int):
    """Verifica se o usuário tem acesso ao projeto (dono ou compartilhado)"""
    projeto = db.query(models.Projeto).options(
        joinedload(models.Projeto.compartilhamentos)
    ).filter(
        models.Projeto.id == projeto_id
    ).first()
    
    if not projeto:
        return False
    
    # Verifica se é dono ou tem compartilhamento
    return (projeto.usuario_id == user_id) or any(
        comp.usuario_id == user_id for comp in projeto.compartilhamentos
    )

@router.get("/criar-tarefa", response_class=HTMLResponse)
async def exibir_formulario_criar_tarefa(
    request: Request, 
    projeto_id: int, 
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

        if not verificar_acesso_projeto(db, user.id, projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Adicione a data atual no formato YYYY-MM-DD
        data_atual = datetime.now().strftime('%Y-%m-%d')

        return templates.TemplateResponse("criar_tarefa.html", {
            "request": request, 
            "projeto_id": projeto_id,
            "prioridades": ["baixa", "media", "alta"],
        })
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.post("/criar-tarefa", response_class=RedirectResponse)
async def criar_tarefa(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    projeto_id: int = Form(...),
    prioridade: str = Form(...),
    data_entrega: str = Form(...),  # Adicione este parâmetro
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

        if not verificar_acesso_projeto(db, user.id, projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Converta a string da data para um objeto date
        data_entrega_obj = datetime.strptime(data_entrega, '%Y-%m-%d').date()

        nova_tarefa = schemas.TarefaCreate(
            nome=nome,
            descricao=descricao,
            projeto_id=projeto_id,
            prioridade=prioridade,
            usuario_id=user.id,
            data_entrega=data_entrega_obj  # Inclua a data de entrega
        )
        crud.create_tarefa(db, nova_tarefa)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

        
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

        tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
        if not tarefa:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")

        if not verificar_acesso_projeto(db, user.id, tarefa.projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        crud.atualizar_status_tarefa(db, tarefa_id=tarefa_id, status=status)
        return RedirectResponse(url="/projetos", status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
@router.get("/tarefas/{tarefa_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_tarefa(
    request: Request, 
    tarefa_id: int, 
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

        tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
        if not tarefa:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")

        if not verificar_acesso_projeto(db, user.id, tarefa.projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        return templates.TemplateResponse("editar_tarefa.html", {
            "request": request, 
            "tarefa": tarefa,
            "prioridades": ["baixa", "media", "alta"]
        })
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.post("/tarefas/{tarefa_id}/editar", response_class=RedirectResponse)
async def editar_tarefa(
    request: Request,
    tarefa_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    prioridade: str = Form(...),
    status: bool = Form(False),  # Mude para False como padrão
    data_entrega: str = Form(None),  # Adicione este campo
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

        tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
        if not tarefa:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")

        if not verificar_acesso_projeto(db, user.id, tarefa.projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Converter a data se for fornecida
        data_entrega_obj = datetime.strptime(data_entrega, '%Y-%m-%d').date() if data_entrega else None

        tarefa_atualizada = schemas.TarefaUpdate(
            nome=nome, 
            descricao=descricao, 
            status=status, 
            prioridade=prioridade,
            data_entrega=data_entrega_obj  # Adicione este campo
        )
        crud.editar_tarefa(db, tarefa_id=tarefa_id, tarefa=tarefa_atualizada)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de data inválido")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

        
@router.delete("/tarefas/{tarefa_id}/excluir", response_model=schemas.Mensagem)
def excluir_tarefa(
    request: Request,
    tarefa_id: int, 
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

        tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
        if not tarefa:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")

        if not verificar_acesso_projeto(db, user.id, tarefa.projeto_id):
            raise HTTPException(status_code=403, detail="Acesso negado")

        sucesso = crud.excluir_tarefa(db, tarefa_id=tarefa_id)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        return {"mensagem": "Tarefa excluída com sucesso"}
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")