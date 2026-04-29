from sqlalchemy.orm import Session, joinedload
from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno
from backend.schemas.aluno import AlunoCreate, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoUpdate


class AlunoService:
    def __init__(self, db: Session):
        self.db = db

    def criar_aluno(self, data: AlunoCreate) -> Aluno:
        aluno = Aluno(**data.model_dump())
        self.db.add(aluno)
        self.db.commit()
        self.db.refresh(aluno)
        return aluno

    def criar_perfil(self, aluno_id: int, data: PerfilAlunoCreate) -> PerfilAluno:
        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            raise ValueError(f"Aluno {aluno_id} não encontrado")

        perfil_existente = self.db.query(PerfilAluno).filter(
            PerfilAluno.aluno_id == aluno_id
        ).first()
        if perfil_existente:
            raise ValueError(f"Aluno {aluno_id} já possui um perfil")
        
        # Cria perfil
        perfil = PerfilAluno(aluno_id=aluno_id, **data.model_dump())
        self.db.add(perfil)
        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def listar_alunos(self, skip: int = 0, limit: int = 100):
        return (
            self.db.query(Aluno)
            .options(joinedload(Aluno.perfil))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def obter_aluno_por_id(self, aluno_id: int) -> Aluno:
        aluno = (
            self.db.query(Aluno)
            .options(joinedload(Aluno.perfil))
            .filter(Aluno.id == aluno_id)
            .first()
        )
        if not aluno:
            raise ValueError(f"Aluno {aluno_id} não encontrado")
        return aluno

    def atualizar_aluno(self, aluno_id: int, data: AlunoUpdate) -> Aluno:
        """Atualiza dados do aluno"""
        aluno = self.obter_aluno_por_id(aluno_id)
        if not aluno:
            raise ValueError(f"Aluno {aluno_id} não encontrado")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(aluno, key, value)
        
        self.db.commit()
        self.db.refresh(aluno)
        return aluno

    def atualizar_perfil(self, aluno_id: int, data: PerfilAlunoUpdate) -> PerfilAluno:
        perfil = (
            self.db.query(PerfilAluno)
            .filter(PerfilAluno.aluno_id == aluno_id)
            .first()
        )
        if not perfil:
            raise ValueError(f"Perfil do aluno {aluno_id} não encontrado")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(perfil, key, value)
        
        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def deletar_aluno(self, aluno_id: int) -> bool:
        aluno = self.db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            return False
        
        self.db.delete(aluno)
        self.db.commit()
        return True
