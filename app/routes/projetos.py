from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from .. import schemas, models
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

        projetos = db.query(models.Projeto).options(
            joinedload(models.Projeto.criador),
            joinedload(models.Projeto.compartilhamentos).joinedload(models.ProjetoCompartilhado.usuario)
        ).filter(
            (models.Projeto.usuario_id == user.id) |
            (models.Projeto.compartilhamentos.any(usuario_id=user.id))
        ).all()

        projetos_com_tarefas = []
        for projeto in projetos:
            tarefas = crud.get_tarefas_por_projeto(db, projeto_id=projeto.id)
            
            compartilhado_por = []
            if projeto.usuario_id != user.id: 
                compartilhado_por = [projeto.criador]
                
            projetos_com_tarefas.append({
                "projeto": projeto,
                "tarefas": tarefas,
                "dono": projeto.usuario_id == user.id,
                "compartilhado_por": compartilhado_por 
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

        # Verifica se o usuário é dono do projeto
        projeto = crud.get_projeto(db, projeto_id=projeto_id)
        if not projeto or projeto.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        projeto_atualizado = schemas.ProjetoUpdate(nome=nome, descricao=descricao)
        crud.editar_projeto(db, projeto_id=projeto_id, projeto=projeto_atualizado)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_projeto(
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

        projeto = crud.get_projeto(db, projeto_id=projeto_id)
        if not projeto or projeto.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        return templates.TemplateResponse(
            "editar_projeto.html", 
            {"request": request, "projeto": projeto}
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/projetos/{projeto_id}/compartilhar", response_class=HTMLResponse)
async def exibir_formulario_compartilhar(
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

        projeto = crud.get_projeto(db, projeto_id=projeto_id)
        if not projeto or projeto.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        return templates.TemplateResponse(
            "compartilhar_projeto.html",
            {"request": request, "projeto": projeto, "user": user}
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.post("/projetos/{projeto_id}/compartilhar", response_class=RedirectResponse)
async def compartilhar_projeto(
    request: Request,
    projeto_id: int,
    email_usuario: str = Form(...),
    permissoes: str = Form(...),
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

        # Verifica se o projeto pertence ao usuário
        projeto = crud.get_projeto(db, projeto_id=projeto_id)
        if not projeto or projeto.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Compartilha o projeto
        compartilhamento = crud.compartilhar_projeto(
            db, 
            projeto_id=projeto_id, 
            usuario_email=email_usuario, 
            permissoes=permissoes
        )
        
        if not compartilhamento:
            raise HTTPException(status_code=400, detail="Não foi possível compartilhar o projeto")

        return RedirectResponse(url=f"/projetos/{projeto_id}/compartilhados", status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/projetos/{projeto_id}/compartilhados", response_class=HTMLResponse)
async def listar_compartilhamentos(
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

        projeto = crud.get_projeto(db, projeto_id=projeto_id)
        if not projeto or projeto.usuario_id != user.id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Obter lista de usuários com quem o projeto foi compartilhado
        compartilhamentos = db.query(models.ProjetoCompartilhado).filter(
            models.ProjetoCompartilhado.projeto_id == projeto_id
        ).all()

        usuarios_compartilhados = []
        for comp in compartilhamentos:
            usuario = crud.get_usuario(db, usuario_id=comp.usuario_id)
            usuarios_compartilhados.append({
                "usuario": usuario,
                "permissoes": comp.permissoes
            })

        return templates.TemplateResponse(
            "compartilhamentos_projeto.html",
            {
                "request": request,
                "projeto": projeto,
                "usuarios_compartilhados": usuarios_compartilhados,
                "user": user
            }
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")