# Acolhe+

**Aplicação web com inteligência artificial para apoio à personalização do ensino de alunos com TEA e TDAH.**

O Acolhe+ ajuda professores e profissionais do NAPNE (Núcleo de Atendimento às Pessoas com Necessidades Educacionais Específicas) a organizar o perfil de aprendizagem dos alunos com Transtorno do Espectro Autista (TEA) e Transtorno do Déficit de Atenção e Hiperatividade (TDAH) e a gerar conteúdos pedagógicos adaptados a esse perfil, com a API do Google Gemini.

Projeto desenvolvido como Trabalho de Conclusão de Curso de Tecnologia em Análise e Desenvolvimento de Sistemas do IFRN, Campus Nova Cruz.

## Funcionalidades

- Login via **SUAP** (OAuth2) e via conta local para membros convidados do NAPNE.
- Importação de alunos do SUAP (ou cadastro manual) e **validação de indicações** pela equipe NAPNE.
- **Perfil de aprendizado** do aluno: nível de atenção, dificuldade de leitura, preferência, interesses e diagnóstico.
- **Geração de conteúdo educacional adaptado** por IA, com histórico e versionamento.
- **Chat com IA** contextualizado ao aluno e/ou à disciplina, com respostas em streaming e anexos.
- **Portal do aluno**, com edição de interesses e preferência de aprendizado.
- **Disciplinas do professor**, com observações pedagógicas, solicitação de apoio ao NAPNE e materiais de apoio.
- Feedback dos professores sobre os conteúdos gerados e notificações.
- Exportação de dados (CSV e PDF), relatórios de uso e exportação de dados pessoais (LGPD).
- Logs de auditoria das operações com dados sensíveis.
- Recursos de acessibilidade: régua de leitura, foco, fonte para dislexia e modo para daltonismo.

## Tecnologias

| Área | Tecnologia |
|---|---|
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| Banco de dados | PostgreSQL, SQLAlchemy, Alembic |
| IA | Google Gemini (`google-generativeai`) |
| Autenticação | OAuth2 do SUAP, JWT, bcrypt |
| Frontend | HTML, CSS e JavaScript puro, marked, DOMPurify |
| Extração de texto | PyMuPDF, python-docx, python-pptx, Pillow e Tesseract OCR (opcional) |

## Como executar

### Pré-requisitos

- Python 3
- PostgreSQL
- Credenciais OAuth2 do SUAP (client id, client secret e URL de retorno)
- Chave da API do Google Gemini
- Tesseract OCR com o idioma português (opcional, para ler imagens e PDFs digitalizados)

### Instalação

```bash
git clone https://github.com/freitas777/acolhe.git
cd acolhe

python -m venv venv
source venv/bin/activate        # no Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão com o PostgreSQL |
| `SECRET_KEY` | Chave de assinatura dos tokens JWT |
| `SUAP_CLIENT_ID`, `SUAP_CLIENT_SECRET` | Credenciais OAuth2 do SUAP |
| `SUAP_REDIRECT_URI` | URL de retorno do login via SUAP |
| `GEMINI_API_KEY` | Chave da API do Gemini |
| `GEMINI_MODEL` | Modelo do Gemini (padrão `gemini-2.5-flash`) |

A lista completa de variáveis está em [docs/documentacao.md](docs/documentacao.md#10-configuração-e-execução).

### Banco de dados e execução

```bash
alembic upgrade head
uvicorn main:app --reload
```

A aplicação fica disponível em `http://localhost:8000`, e a documentação interativa da API em `http://localhost:8000/docs`.

### Scripts utilitários

| Script | Função |
|---|---|
| `scripts/create_admin.py` | Cria um usuário administrador com conta local (`python -m scripts.create_admin`; pede e-mail, senha e nome). |
| `scripts/seed_demo.py` | Cria dados de demonstração para professor e NAPNE (`python -m scripts.seed_demo`). |
| `scripts/backfill_pendencias.py` | Cria pendências de validação para alunos que ainda não têm (`python -m scripts.backfill_pendencias`). |
| `scripts/backfill_materiais_texto.py` | Extrai o texto de materiais já enviados. |

## Perfis de usuário

| Perfil | O que faz |
|---|---|
| Aluno | Vê o perfil e os conteúdos, edita preferências e conversa com a IA. |
| Professor | Vê suas turmas, solicita apoio, registra observações e avalia conteúdos. |
| Psicopedagogo | Importa alunos, valida indicações, cadastra perfis, gera conteúdos e convida membros. |
| Servidor | Atua na equipe NAPNE, sem convidar novos membros. |
| Administrador | Acesso total, incluindo a desativação de contas. |

## Estrutura do projeto

```
acolhe/
├── main.py          # Aplicação FastAPI
├── backend/         # Routers, services, repositories, schemas e models
├── frontend/        # Páginas HTML, CSS e JavaScript
├── migrations/      # Migrações do Alembic
├── scripts/         # Scripts utilitários
├── testes/          # Configuração de testes
└── docs/            # Documentação, requisitos e diagramas
```

## Documentação

- [Arquitetura](docs/arquitetura.md): camadas, componentes, IA, segurança, fluxos e implantação.
- [Documentação](docs/documentacao.md): requisitos, casos de uso, histórias de usuário, modelo de dados e API.
- [Requisitos](docs/requisitos/): especificações detalhadas.

## Testes

O projeto usa `pytest` (com `pytest-asyncio`, `pytest-mock` e `pytest-cov`), e a configuração base está em `testes/conftest.py`:

```bash
pytest
```

## Implantação

O `Procfile` aplica as migrações e inicia o servidor. O `build.sh` instala as dependências, tenta instalar o Tesseract e executa as migrações.

## Contexto acadêmico

- **Autor:** Lucas Freitas dos Santos
- **Orientador:** Prof. Fábio Fernandes Penha
- **Instituição:** Instituto Federal de Educação, Ciência e Tecnologia do Rio Grande do Norte (IFRN), Campus Nova Cruz
- **Curso:** Tecnologia em Análise e Desenvolvimento de Sistemas