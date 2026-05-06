
# Importação de Alunos via SUAP para Acompanhamento

**COMO** membro gestor da equipe multidisciplinar do NAPNE,  
**QUERO** pesquisar alunos na base de dados do SUAP por nome ou matrícula,  
**PARA** importá-los para o Acolhe+ e iniciar o processo de indicação de acompanhamento.  

## Critérios de Aceitação

1. O acesso deve ser restrito a perfis identificados pelo SUAP como servidores vinculados ao NAPNE ou com as atribuições técnicas necessárias.
2. O sistema deve oferecer um campo de busca onde o profissional possa digitar o nome completo ou o número da matrícula do aluno.
3. Ao realizar a busca, o sistema deve consultar a API do SUAP e retornar uma lista de resultados contendo: Nome, Foto (**se disponível**), Matrícula, Curso e Campus.
4. Caso o aluno já tenha sido importado anteriormente para o Acolhe+, o sistema deve indicar claramente seu status (Ex: "Já em acompanhamento" ou "Pendente de validação") e desabilitar o botão de nova importação.
5. Ao selecionar um aluno, o sistema deve copiar os dados cadastrais essenciais do SUAP para a base local do Acolhe+, criando o registro inicial do aluno com o status "Aguardando Indicação".
6. Por padrão, a busca deve privilegiar alunos do mesmo campus do servidor logado, mas permitir a busca em todo o instituto se necessário.  
