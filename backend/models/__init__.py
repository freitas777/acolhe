from backend.models.usuario import Usuario
from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.models.disciplina import Disciplina
from backend.models.diario_aluno import DiarioAluno
from backend.models.pendencia_validacao import PendenciaValidacao
from backend.models.conta_local import ContaLocal
from backend.models.notificacao import Notificacao, NotificacaoLeitura

__all__ = [
    "Usuario",
    "Aluno",
    "PerfilAluno",
    "ConteudoGerado",
    "Conversa",
    "Mensagem",
    "Disciplina",
    "DiarioAluno",
    "PendenciaValidacao",
    "ContaLocal",
    "Notificacao",
    "NotificacaoLeitura",
]
