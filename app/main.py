from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth
from .database import engine, get_db
from .auth import SECRET_KEY, ALGORITHM, verify_password, create_access_token, get_current_user
from jose import JWTError, jwt

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=RedirectResponse)
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

@app.get("/projetos", response_class=HTMLResponse)
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
            {"request": request, "user": user, "projetos_com_tarefas": projetos_com_tarefas,  "show_nav": True}
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=RedirectResponse)
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

@app.get("/criar-projeto", response_class=HTMLResponse)
async def exibir_formulario_criar_projeto(request: Request):
    return templates.TemplateResponse("criar_projeto.html", {"request": request})

@app.post("/criar-projeto", response_class=RedirectResponse)
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

@app.delete("/projetos/{projeto_id}/excluir", response_model=schemas.Mensagem)
def excluir_projeto(projeto_id: int, db: Session = Depends(get_db)):
    sucesso = crud.excluir_projeto(db, projeto_id=projeto_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return {"mensagem": "Projeto excluído com sucesso"}
    

@app.post("/projetos/{projeto_id}/editar", response_class=RedirectResponse)
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

@app.get("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_projeto(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    projeto = crud.get_projeto(db, projeto_id=projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return templates.TemplateResponse("editar_projeto.html", {"request": request, "projeto": projeto})

@app.get("/criar-tarefa", response_class=HTMLResponse)
async def exibir_formulario_criar_tarefa(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse("criar_tarefa.html", {
        "request": request, 
        "projeto_id": projeto_id,
        "prioridades": ["baixa", "media", "alta"]  # Adicione esta linha
    })

@app.post("/criar-tarefa", response_class=RedirectResponse)
async def criar_tarefa(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    projeto_id: int = Form(...),
    prioridade: str = Form(...),  # Adicione este parâmetro
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
            prioridade=prioridade,  # Adicione esta linha
            usuario_id=user.id
        )
        crud.create_tarefa(db, nova_tarefa)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@app.post("/tarefas/{tarefa_id}/status", response_class=RedirectResponse)
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

        crud.atualizar_status_tarefa(db, tarefa_id=tarefa_id, status=status)

        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "success", "tarefa_id": tarefa_id, "novo_status": status})
            
@app.get("/tarefas/{tarefa_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_tarefa(request: Request, tarefa_id: int, db: Session = Depends(get_db)):
    tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return templates.TemplateResponse("editar_tarefa.html", {"request": request, "tarefa": tarefa})

@app.post("/tarefas/{tarefa_id}/editar", response_class=RedirectResponse)
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

        
@app.delete("/tarefas/{tarefa_id}/excluir", response_model=schemas.Mensagem)
def excluir_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    sucesso = crud.excluir_tarefa(db, tarefa_id=tarefa_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"mensagem": "Tarefa excluída com sucesso"}

@app.get("/perfil", response_class=HTMLResponse)
async def perfil(
    request: Request,
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

        # Obter estatísticas do usuário
        projetos_count = crud.get_projetos_count(db, user.id)
        tarefas_count = crud.get_tarefas_count(db, user.id)
        tarefas_concluidas = crud.get_tarefas_concluidas_count(db, user.id)
        tarefas_pendentes = tarefas_count - tarefas_concluidas
        tarefas_prioridade = crud.get_tarefas_por_prioridade(db, user.id)
        tarefas_recentes = crud.get_tarefas_recentes(db, user.id, limit=5)

        return templates.TemplateResponse(
            "perfil.html",
            {
                "request": request,
                "user": user,
                "projetos_count": projetos_count,
                "tarefas_count": tarefas_count,
                "tarefas_concluidas": tarefas_concluidas,
                "tarefas_pendentes": tarefas_pendentes,
                "tarefas_prioridade": tarefas_prioridade,
                "tarefas_recentes": tarefas_recentes,
                 "show_nav": True
            }
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")