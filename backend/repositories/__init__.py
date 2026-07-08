from backend.repositories.aluno import AlunoRepository
from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository
from backend.repositories.conta_local import ContaLocalRepository
from backend.repositories.conteudo_gerado import ConteudoGeradoRepository
from backend.repositories.conversa import ConversaRepository
from backend.repositories.diario_aluno import DiarioAlunoRepository
from backend.repositories.disciplina import DisciplinaRepository
from backend.repositories.mensagem import MensagemRepository
from backend.repositories.notificacao import NotificacaoRepository
from backend.repositories.pendencia_validacao import PendenciaValidacaoRepository
from backend.repositories.perfil_aluno import PerfilAlunoRepository
from backend.repositories.usuario import UsuarioRepository

__all__ = [
    "AlunoRepository",
    "AcomodacaoObservacaoRepository",
    "ContaLocalRepository",
    "ConteudoGeradoRepository",
    "ConversaRepository",
    "DiarioAlunoRepository",
    "DisciplinaRepository",
    "MensagemRepository",
    "NotificacaoRepository",
    "PendenciaValidacaoRepository",
    "PerfilAlunoRepository",
    "UsuarioRepository",
]
