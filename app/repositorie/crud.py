from sqlalchemy.orm import Session
from datetime import date
from .. import models, schemas
from ..auth import get_password_hash

#usuário
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


def editar_usuario(db: Session, usuario_id: int, usuario: schemas.UsuarioUpdate):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if db_usuario:
        if usuario.nome:
            db_usuario.nome = usuario.nome
        if usuario.email:
            db_usuario.email = usuario.email
        if usuario.senha:
            db_usuario.senha_hash = get_password_hash(usuario.senha)
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

    
#projeto
def get_projeto(db: Session, projeto_id: int):
    return db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()

def get_projetos(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Projeto).filter(models.Projeto.usuario_id == usuario_id).offset(skip).limit(limit).all()

def create_projeto(db: Session, projeto: schemas.ProjetoCreate):
    db_projeto = models.Projeto(
        nome=projeto.nome,
        descricao=projeto.descricao,
        usuario_id=projeto.usuario_id
    )
    db.add(db_projeto)
    db.commit()
    db.refresh(db_projeto)
    return db_projeto

def excluir_projeto(db: Session, projeto_id: int):
    db_projeto = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if db_projeto:
        db.query(models.Tarefa).filter(models.Tarefa.projeto_id == projeto_id).delete()
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


  # Tarefa
def get_tarefas_por_projeto(db: Session, projeto_id: int):
    return db.query(models.Tarefa).filter(models.Tarefa.projeto_id == projeto_id).all()

def create_tarefa(db: Session, tarefa: schemas.TarefaCreate):
    db_tarefa = models.Tarefa(
        nome=tarefa.nome,
        descricao=tarefa.descricao,
        status=tarefa.status,
        projeto_id=tarefa.projeto_id,
        usuario_id=tarefa.usuario_id,
        prioridade=tarefa.prioridade.value if hasattr(tarefa.prioridade, 'value') else tarefa.prioridade,
        data_entrega=tarefa.data_entrega
    )
    db.add(db_tarefa)
    db.commit()
    db.refresh(db_tarefa)
    return db_tarefa

def editar_tarefa(db: Session, tarefa_id: int, tarefa: schemas.TarefaUpdate):
    db_tarefa = db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
    if db_tarefa:
        if tarefa.nome is not None:
            db_tarefa.nome = tarefa.nome
        if tarefa.descricao is not None:
            db_tarefa.descricao = tarefa.descricao
        if tarefa.status is not None:
            db_tarefa.status = tarefa.status
        if tarefa.prioridade is not None:
            db_tarefa.prioridade = tarefa.prioridade.value if hasattr(tarefa.prioridade, 'value') else tarefa.prioridade
        if tarefa.data_entrega is not None:
            db_tarefa.data_entrega = tarefa.data_entrega
        if tarefa.data_entrega is not None:
            db_tarefa.data_entrega = tarefa.data_entrega
        db.commit()
        db.refresh(db_tarefa)
    return db_tarefa

def excluir_tarefa(db: Session, tarefa_id: int):
    db_tarefa = db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
    if db_tarefa:
        db.delete(db_tarefa)
        db.commit()
        return True
    return False

def get_tarefa(db: Session, tarefa_id: int):
    return db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()

def atualizar_status_tarefa(db: Session, tarefa_id: int, status: bool):
    db_tarefa = db.query(models.Tarefa).filter(models.Tarefa.id == tarefa_id).first()
    if not db_tarefa:
        return False
    db_tarefa.status = status
    db.commit()
    db.refresh(db_tarefa)
    return True

# Novas funções para filtrar tarefas por status de atraso
def get_tarefas_atrasadas(db: Session, usuario_id: int):
    return db.query(models.Tarefa).filter(
        models.Tarefa.usuario_id == usuario_id,
        models.Tarefa.status == False,
        models.Tarefa.data_entrega < date.today()
    ).all()

def get_tarefas_para_hoje(db: Session, usuario_id: int):
    return db.query(models.Tarefa).filter(
        models.Tarefa.usuario_id == usuario_id,
        models.Tarefa.status == False,
        models.Tarefa.data_entrega == date.today()
    ).all()

def get_tarefas_por_periodo(db: Session, usuario_id: int, data_inicio: date, data_fim: date):
    return db.query(Tarefa).filter(
        Tarefa.usuario_id == usuario_id,
        Tarefa.data_entrega >= data_inicio,
        Tarefa.data_entrega <= data_fim
    ).all()


def get_projetos_count(db: Session, usuario_id: int):
    return db.query(models.Projeto).filter(models.Projeto.usuario_id == usuario_id).count()

def get_tarefas_count(db: Session, usuario_id: int):
    return db.query(models.Tarefa).filter(models.Tarefa.usuario_id == usuario_id).count()

def get_tarefas_concluidas_count(db: Session, usuario_id: int):
    return db.query(models.Tarefa).filter(
        models.Tarefa.usuario_id == usuario_id,
        models.Tarefa.status == True 
    ).count()

def get_tarefas_por_prioridade(db: Session, usuario_id: int):
    return {
        'alta': db.query(models.Tarefa).filter(
            models.Tarefa.usuario_id == usuario_id,
            models.Tarefa.prioridade == 'alta'
        ).count(),
        'media': db.query(models.Tarefa).filter(
            models.Tarefa.usuario_id == usuario_id,
            models.Tarefa.prioridade == 'media'
        ).count(),
        'baixa': db.query(models.Tarefa).filter(
            models.Tarefa.usuario_id == usuario_id,
            models.Tarefa.prioridade == 'baixa'
        ).count()
    }

def get_tarefas_recentes(db: Session, usuario_id: int, limit: int = 5):
    return db.query(models.Tarefa).filter(
        models.Tarefa.usuario_id == usuario_id
    ).order_by(models.Tarefa.id.desc()).limit(limit).all()



def compartilhar_projeto(db: Session, projeto_id: int, usuario_email: str, permissoes: str):
    projeto = db.query(models.Projeto).filter(models.Projeto.id == projeto_id).first()
    if not projeto:
        return None
    
    usuario = get_usuario_by_email(db, email=usuario_email)
    if not usuario:
        return None
    
    existente = db.query(models.ProjetoCompartilhado).filter(
        models.ProjetoCompartilhado.projeto_id == projeto_id,
        models.ProjetoCompartilhado.usuario_id == usuario.id
    ).first()
    
    if existente:
        return None
    
    db_compartilhamento = models.ProjetoCompartilhado(
        projeto_id=projeto_id,
        usuario_id=usuario.id,
        permissoes=permissoes
    )
    
    db.add(db_compartilhamento)
    db.commit()
    db.refresh(db_compartilhamento)
    return db_compartilhamento

def get_projetos_compartilhados(db: Session, usuario_id: int):
    return db.query(models.Projeto).join(
        models.ProjetoCompartilhado,
        models.ProjetoCompartilhado.projeto_id == models.Projeto.id
    ).filter(
        models.ProjetoCompartilhado.usuario_id == usuario_id
    ).all()

def get_projetos_do_usuario(db: Session, usuario_id: int):
    projetos_proprios = db.query(models.Projeto).filter(
        models.Projeto.usuario_id == usuario_id
    ).all()
    
    projetos_compartilhados = get_projetos_compartilhados(db, usuario_id)
    
    return projetos_proprios + projetos_compartilhados


def calcular_projetos_compartilhados(user_id):
    from models import Projeto, ProjetoCompartilhado
    
    return db.session.query(Projeto).join(
        ProjetoCompartilhado,
        ProjetoCompartilhado.projeto_id == Projeto.id
    ).filter(
        ProjetoCompartilhado.usuario_id == user_id,
        Projeto.usuario_id != user_id
    ).count()

def get_projetos_compartilhados_count(db: Session, usuario_id: int) -> int:
    return db.query(models.ProjetoCompartilhado).filter(
        models.ProjetoCompartilhado.usuario_id == usuario_id,
        models.ProjetoCompartilhado.projeto.has(models.Projeto.usuario_id != usuario_id)
    ).count()