# Plano: Exportação de Relatório Individual do Aluno em PDF

## Objetivo
Permitir que o NAPNE gere um relatório PDF individual de cada aluno contendo perfil pedagógico, histórico de conteúdos gerados pela IA, observações dos professores e materiais das disciplinas. Útil para reuniões com família e documentação.

## Estado Atual
- Já existe endpoint `GET /api/relatorios/uso/csv` (relatório geral do sistema em CSV)
- Já existe botão "Relatório de Uso" no painel (baixa CSV geral)
- Já existe modal de perfil do aluno (`profile-modal`) no painel
- **Não existe** geração de PDF nem relatório individual por aluno

## Decisões de Design

### Onde colocar o botão?
- **Dentro do modal de perfil do aluno** (`profile-modal`) — ao lado do botão "Salvar Perfil"
- Faz sentido: o NAPNE abre o perfil do aluno e quer gerar o relatório daquele aluno específico

### O que incluir no PDF?
1. **Cabeçalho**: Logo Acolhe+, data de geração, nome do aluno, matrícula, curso, campus
2. **Perfil Pedagógico**: nível de atenção, dificuldade de leitura, preferência de aprendizado, interesses, diagnóstico
3. **Conteúdos Gerados pela IA**: lista com tema, data, modelo IA usado, resumo do conteúdo
4. **Observações dos Professores**: texto da observação, disciplina, professor, data
5. **Materiais das Disciplinas**: lista de materiais vinculados às disciplinas do aluno (via DiarioAluno)
6. **Histórico de Conversas**: resumo das conversas (título, data, disciplina vinculada)

### Biblioteca PDF
- **WeasyPrint** — converte HTML/CSS para PDF profissional
- Permite criar template HTML bonito com CSS e gerar PDF de alta qualidade
- Suporta paginação, headers/footers, fontes Unicode (acentos)

## Implementação

### 1. Dependência — `requirements.txt`
Adicionar:
```
weasyprint==62.3
```

### 2. Backend — `backend/routers/relatorios.py`
Novo endpoint:
```python
@router.get("/aluno/{aluno_id}/pdf")
async def relatorio_aluno_pdf(
    aluno_id: int,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
```

Lógica:
1. Buscar `Aluno` com `selectinload(Aluno.perfil)`
2. Buscar `ConteudoGerado` do aluno (ordenado por data)
3. Buscar `AcomodacaoObservacao` do aluno (com disciplina e professor)
4. Buscar `DiarioAluno` do aluno → disciplinas → `Material` de cada disciplina
5. Buscar `Conversa` do aluno (com disciplina)
6. Renderizar template HTML com todos os dados
7. Converter HTML para PDF com WeasyPrint
8. Retornar `StreamingResponse` com `media_type="application/pdf"`

### 3. Template HTML — `backend/templates/relatorio_aluno.html`
Template HTML com CSS inline (WeasyPrint requer CSS inline ou embutido):
- Layout profissional com cabeçalho, seções bem definidas
- Cores institucionais (verde SUAP)
- Paginção com `@page` CSS
- Suporte completo a caracteres Unicode

### 4. Frontend — `frontend/painel.html`
Adicionar botão no modal-actions do `profile-modal`:
```html
<button type="button" class="btn-modal-pdf" id="btn-gerar-relatorio-pdf">
  Gerar Relatório PDF
</button>
```

### 5. Frontend — `frontend/js/painel.js`
Adicionar função `gerarRelatorioPDF()`:
- Obter `alunoId` do campo hidden `profile-aluno-id`
- Chamar `GET /api/relatorios/aluno/{alunoId}/pdf` com `responseType: 'blob'`
- Criar link temporário e fazer download do PDF
- Mostrar toast de sucesso/erro

### 6. Frontend — `frontend/css/painel.css`
Adicionar estilo para o botão de PDF:
```css
.btn-modal-pdf { ... }
```

## Arquivos Afetados

| Arquivo | Ação |
|---------|------|
| `requirements.txt` | Adicionar `weasyprint` |
| `backend/routers/relatorios.py` | Adicionar endpoint `/aluno/{aluno_id}/pdf` |
| `backend/templates/relatorio_aluno.html` | Criar template HTML do relatório |
| `frontend/painel.html` | Adicionar botão "Gerar Relatório PDF" no modal |
| `frontend/js/painel.js` | Adicionar função `gerarRelatorioPDF()` |
| `frontend/css/painel.css` | Estilizar botão PDF |

## Ordem de Implementação
1. Instalar `weasyprint` e adicionar ao `requirements.txt`
2. Criar template HTML `backend/templates/relatorio_aluno.html`
3. Adicionar endpoint `/aluno/{aluno_id}/pdf` no `relatorios.py`
4. Adicionar botão no modal de perfil (`painel.html`)
5. Adicionar função JS (`painel.js`)
6. Adicionar estilos CSS (`painel.css`)
7. Verificar servidor inicia e teste manual

## Validação
- [ ] NAPNE abre perfil de um aluno no painel
- [ ] Botão "Gerar Relatório PDF" aparece no modal
- [ ] Clique no botão gera download de PDF
- [ ] PDF contém: dados do aluno, perfil pedagógico, conteúdos gerados, observações, materiais
- [ ] PDF tem formatação profissional (cabeçalho, seções, paginação)
- [ ] PDF suporta caracteres especiais (acentos, ç)
- [ ] Aluno sem perfil gera PDF com seção "Sem perfil cadastrado"
- [ ] Aluno sem conteúdos gera PDF com seção "Nenhum conteúdo gerado"
- [ ] Endpoint requer permissão NAPNE (403 para não-autorizados)

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| WeasyPrint depende de GTK3 (instalação complexa no Windows) | Usar versão pré-compilada; fallback para `xhtml2pdf` se necessário |
| PDF muito grande para alunos com muito histórico | Limitar a últimos 50 conteúdos gerados |
| Template HTML complexo | Manter CSS simples e inline, testar renderização |
| WeasyPrint lento para muitos alunos | Geração é sob demanda (um aluno por vez), não batch |

## Fallback: xhtml2pdf
Se WeasyPrint tiver problemas de instalação no Windows, usar `xhtml2pdf` como alternativa:
- Pure Python, sem dependências nativas
- Menos recursos CSS que WeasyPrint, mas suficiente para este caso
- `pip install xhtml2pdf`
