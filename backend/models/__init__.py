from backend.models.usuario import Usuario
from backend.models.conta_local import ContaLocal
from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno
from backend.models.disciplina import Disciplina
from backend.models.diario_aluno import DiarioAluno
from backend.models.pendencia_validacao import PendenciaValidacao
from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.acomodacao_observacao import AcomodacaoObservacao
from backend.models.audit_log import AuditLog
from backend.models.conteudo_feedback import ConteudoFeedback
from backend.models.material import Material
from backend.models.notificacao import Notificacao, NotificacaoLeitura
from backend.models.token_revogado import TokenRevogado

__all__ = [
    "Usuario",
    "ContaLocal",
    "Aluno",
    "PerfilAluno",
    "Disciplina",
    "DiarioAluno",
    "PendenciaValidacao",
    "Conversa",
    "Mensagem",
    "ConteudoGerado",
    "AcomodacaoObservacao",
    "AuditLog",
    "ConteudoFeedback",
    "Material",
    "Notificacao",
    "NotificacaoLeitura",
    "TokenRevogado",
]
