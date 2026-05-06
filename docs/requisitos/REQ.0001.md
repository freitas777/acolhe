
# Login e Sincronização Automática de Disciplinas

**COMO** aluno do IFRN,  
**QUERO** realizar o login no Acolhe+ utilizando minhas credenciais do SUAP,  
**PARA** visualizar automaticamente as disciplinas que estou cursando no semestre atual sem precisar cadastrá-las manualmente.

## Critérios de Aceitação

1. O sistema deve autenticar o usuário através do serviço de autenticação do SUAP e validar as credenciais.  
1.1 Se for o primeiro acesso, o sistema deve criar o perfil do aluno no banco de dados do Acolhe+, importando Nome Completo, Matrícula, E-mail Institucional e Campus.  
2. O sistema deve consultar a API do SUAP para buscar a lista de disciplinas em que o aluno está matriculado no período letivo vigente.  
2.1 O sistema deve atualizar essa lista a cada novo login para garantir que trancamentos ou novas matrículas sejam refletidos.  
3. Após o login, o aluno deve ser direcionado para uma tela inicial (Dashboard) com as disciplinas matriculadas.  
3.1 As disciplinas devem ser exibidas em cards individuais (estilo Google Sala de Aula), contendo o nome da disciplina e o nome do professor responsável.  
4. Caso o SUAP esteja fora do ar, o sistema deve exibir uma mensagem amigável informando que a sincronização não foi possível no momento.  
