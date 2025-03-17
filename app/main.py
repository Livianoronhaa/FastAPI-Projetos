from fastapi import FastAPI, Depends, HTTPException, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth
from .database import engine, get_db
from .auth import SECRET_KEY, ALGORITHM, verify_password, create_access_token, get_current_user
from jose import JWTError, jwt

# Configuração do FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Cria as tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# Rota para a página de login
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Rota para processar o formulário de login
@app.post("/login", response_class=RedirectResponse)
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.get_usuario_by_email(db, email=email)
    if not user or not verify_password(password, user.senha_hash):
        raise HTTPException(status_code=400, detail="Email ou senha incorretos")

    # Gera o token JWT
    access_token = create_access_token(data={"sub": user.email})

    # Redireciona para a página de projetos e define o token em um cookie
    response = RedirectResponse(url="/projetos", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

# Rota para a página de projetos
@app.get("/projetos", response_class=HTMLResponse)
async def projetos(request: Request, db: Session = Depends(get_db)):
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Busca os projetos do usuário autenticado
        projetos = crud.get_projetos(db, usuario_id=user.id)

        # Para cada projeto, busca as tarefas associadas
        projetos_com_tarefas = []
        for projeto in projetos:
            tarefas = crud.get_tarefas_por_projeto(db, projeto_id=projeto.id)
            projetos_com_tarefas.append({
                "projeto": projeto,
                "tarefas": tarefas
            })

        return templates.TemplateResponse(
            "projetos.html",
            {"request": request, "user": user, "projetos_com_tarefas": projetos_com_tarefas}
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

# Rota para a página de cadastro
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Rota para processar o formulário de cadastro
@app.post("/register", response_class=RedirectResponse)
async def register(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    # Verifica se o e-mail já está cadastrado
    db_usuario = crud.get_usuario_by_email(db, email=email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    # Cria um novo usuário
    novo_usuario = schemas.UsuarioCreate(nome=nome, email=email, senha=senha)
    crud.create_usuario(db, novo_usuario)

    # Redireciona para a página de login
    return RedirectResponse(url="/", status_code=303)

# Rota para exibir o formulário de criação de projetos
@app.get("/criar-projeto", response_class=HTMLResponse)
async def exibir_formulario_criar_projeto(request: Request):
    return templates.TemplateResponse("criar_projeto.html", {"request": request})

# Rota para processar o formulário de criação de projetos
@app.post("/criar-projeto", response_class=RedirectResponse)
async def criar_projeto(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    db: Session = Depends(get_db)
):
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Cria um novo projeto associado ao usuário
        novo_projeto = schemas.ProjetoCreate(
            nome=nome,
            descricao=descricao,
            usuario_id=user.id  # Associa o projeto ao usuário autenticado
        )
        crud.create_projeto(db, novo_projeto)

        # Redireciona para a página de projetos
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
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Atualiza o projeto
        projeto_atualizado = schemas.ProjetoUpdate(nome=nome, descricao=descricao)
        crud.editar_projeto(db, projeto_id=projeto_id, projeto=projeto_atualizado)

        # Redireciona para a página de projetos
        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@app.get("/projetos/{projeto_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_projeto(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    # Busca o projeto no banco de dados
    projeto = crud.get_projeto(db, projeto_id=projeto_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return templates.TemplateResponse("editar_projeto.html", {"request": request, "projeto": projeto})

# Rota para exibir o formulário de criação de tarefas
@app.get("/criar-tarefa", response_class=HTMLResponse)
async def exibir_formulario_criar_tarefa(request: Request, projeto_id: int, db: Session = Depends(get_db)):
    return templates.TemplateResponse("criar_tarefa.html", {"request": request, "projeto_id": projeto_id})

# Rota para processar o formulário de criação de tarefas
@app.post("/criar-tarefa", response_class=RedirectResponse)
async def criar_tarefa(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    projeto_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Cria uma nova tarefa associada ao projeto e ao usuário
        nova_tarefa = schemas.TarefaCreate(
            nome=nome,
            descricao=descricao,
            projeto_id=projeto_id,
            usuario_id=user.id
        )
        crud.create_tarefa(db, nova_tarefa)

        # Redireciona para a página de projetos
        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

        # Rota para atualizar o status da tarefa
@app.post("/tarefas/{tarefa_id}/status", response_class=RedirectResponse)
async def atualizar_status_tarefa(
    request: Request,
    tarefa_id: int,
    status: bool = Form(...),
    db: Session = Depends(get_db)
):
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Atualiza o status da tarefa
        crud.atualizar_status_tarefa(db, tarefa_id=tarefa_id, status=status)

        # Redireciona para a página de projetos
        redirect_url = f"/projetos?access_token={access_token}"
        return RedirectResponse(url=redirect_url, status_code=303)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    # Retorna uma resposta JSON para o JavaScript
    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "success", "tarefa_id": tarefa_id, "novo_status": status})
            
# Rota para exibir o formulário de edição de tarefa
@app.get("/tarefas/{tarefa_id}/editar", response_class=HTMLResponse)
async def exibir_formulario_editar_tarefa(request: Request, tarefa_id: int, db: Session = Depends(get_db)):
    # Busca a tarefa no banco de dados
    tarefa = crud.get_tarefa(db, tarefa_id=tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return templates.TemplateResponse("editar_tarefa.html", {"request": request, "tarefa": tarefa})

# Rota para processar o formulário de edição de tarefa
@app.post("/tarefas/{tarefa_id}/editar", response_class=RedirectResponse)
async def editar_tarefa(
    request: Request,
    tarefa_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    status: bool = Form(...),
    db: Session = Depends(get_db)
):
    # Obtém o token do cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Token de acesso não fornecido")

    try:
        # Valida o token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Busca o usuário no banco de dados
        user = crud.get_usuario_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")

        # Atualiza a tarefa
        tarefa_atualizada = schemas.TarefaUpdate(nome=nome, descricao=descricao, status=status)
        crud.editar_tarefa(db, tarefa_id=tarefa_id, tarefa=tarefa_atualizada)

        # Redireciona para a página de projetos
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