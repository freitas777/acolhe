
# Login e Diários de Classe via SUAP

**COMO** professor do IFRN,  
**QUERO** acessar o Acolhe+ com minhas credenciais do SUAP,  
**PARA** visualizar todos os meus diários e ementas do semestre de forma organizada e identificar quais turmas possuem alunos assistidos pela equipe psicopedagógica.

## Critérios de Aceitação

1. O login deve ser realizado via integração SUAP, identificando o papel (vínculo) de "Servidor/Professor".    
1.1 Se for o primeiro acesso, o sistema deve criar o perfil do "Servidor/Professor" no banco de dados do Acolhe+, importando Nome Completo, Matrícula, E-mail Institucional e Campus.  
2. O sistema deve consumir a API do SUAP para listar todos os diários/turmas vinculados ao CPF do professor no semestre atual.  
2.1 Deve importar o nome da disciplina, o código da turma (ex: 1.1001.1V) e a ementa simplificada, **se disponível**.  
3. Após o login, o professor deve visualizar _cards_. No entanto, cada _card_ representa uma Turma/Disciplina contendo aluno(s) assistido(s) pela equipe psicopedagógica.  
3.1 Cada _card_ deve exibir um resumo com os seguintes dados : nome da disciplina, o código da turma e a quantidade de aluno(s) assistido(s) pela equipe psicopedagógica.  
4. Ao clicar em um _card_ de disciplina, o professor deve ser levado a uma lista com todos os alunos, daquela turma, assistidos pela equipe psicopedagógica.  

