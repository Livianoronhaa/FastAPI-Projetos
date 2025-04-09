from fastapi import APIRouter
from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .projetos import router as projetos_router
from .tarefas import router as tarefas_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(usuarios_router)
router.include_router(projetos_router)
router.include_router(tarefas_router)