from sqlalchemy.orm import Session
from . import models, schemas, auth
from .auth import get_password_hash

# Operações relacionadas ao usuário
def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    senha_hash = get_password_hash(usuario.senha)
    db_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_hash
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# Operações relacionadas ao projeto
def get_projeto(db: Session, projeto_id: int):
    return db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()

def get_projetos(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Projeto).filter(models.Projeto.usuario_id == usuario_id).offset(skip).limit(limit).all()

def create_projeto(db: Session, projeto: schemas.ProjetoCreate):
    db_projeto = models.Projeto(
        nome=projeto.nome,
        descricao=projeto.descricao,
        usuario_id=projeto.usuario_id  # Associa o projeto ao usuário
    )
    db.add(db_projeto)
    db.commit()
    db.refresh(db_projeto)
    return db_projeto

def excluir_projeto(db: Session, projeto_id: int):
    db_projeto = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if db_projeto:
        # Exclui todas as tarefas associadas ao projeto
        db.query(models.Tarefa).filter(models.Tarefa.projeto_id == projeto_id).delete()
        # Exclui o projeto
        db.delete(db_projeto)
        db.commit()
        return True
    return False

def editar_projeto(db: Session, projeto_id: int, projeto: schemas.ProjetoUpdate):
    db_projeto = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if db_projeto:
        db_projeto.nome = projeto.nome
        db_projeto.descricao = projeto.descricao
        db.commit()
        db.refresh(db_projeto)
    return db_projeto

# Operações relacionadas à tarefa
def get_tarefas_por_projeto(db: Session, projeto_id: int):
    return db.query(models.Tarefa).filter(models.Tarefa.projeto_id == projeto_id).all()

def create_tarefa(db: Session, tarefa: schemas.TarefaCreate):
    db_tarefa = models.Tarefa(
        nome=tarefa.nome,
        descricao=tarefa.descricao,
        status=tarefa.status,
        projeto_id=tarefa.projeto_id,
        usuario_id=tarefa.usuario_id
    )
    db.add(db_tarefa)
    db.commit()
    db.refresh(db_tarefa)
    return db_tarefa


def editar_tarefa(db: Session, tarefa_id: int, tarefa: schemas.TarefaUpdate):
    db_tarefa = db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
    if db_tarefa:
        db_tarefa.nome = tarefa.nome
        db_tarefa.descricao = tarefa.descricao
        db_tarefa.status = tarefa.status
        db.commit()
        db.refresh(db_tarefa)
    return db_tarefa

    # Operações relacionadas à tarefa
def excluir_tarefa(db: Session, tarefa_id: int):
    db_tarefa = db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
    if db_tarefa:
        db.delete(db_tarefa)
        db.commit()
        return True
    return False

def get_tarefa(db: Session, tarefa_id: int):
    return db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
