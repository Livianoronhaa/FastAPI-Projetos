from enum import Enum as PythonEnum
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, Enum
from datetime import date
from app.database import Base
class Prioridade(str, PythonEnum):
    BAIXA = 'baixa'
    MEDIA = 'media'
    ALTA = 'alta'

class Tarefa(Base):
    __tablename__ = "tarefas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(Boolean, default=False)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    prioridade = Column(
        Enum('baixa', 'media', 'alta', name='prioridade_enum'),
        server_default='baixa',
        nullable=False
    )
    data_entrega = Column(Date, nullable=True)
    
    @property
    def atrasada(self):
        if self.data_entrega and not self.status:
            return self.data_entrega < date.today()
        return False