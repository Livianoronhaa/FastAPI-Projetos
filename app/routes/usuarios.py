from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..repositorie import crud
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM, get_current_user
from jose import JWTError, jwt
from ..config import templates

router = APIRouter()

@router.get("/perfil", response_class=HTMLResponse)
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