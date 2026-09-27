
# CITEX | Back end

> Projeto criado como parte das exigências para a conclusão do sprint Back End Avançado **Especialização em Desenvolvimento Full Stack** da **PUC Rio**.

**Citex** é um app simples de gerenciamento de fichamento em formato *Single Page Application*. Consiste de um *front end* criado em HTML, CSS (componentes Bootstrap) e Javascript, alimentado por um *back end* com uma API em Python e um banco de dados em SQLite.

A **API** foi criada em Python, com auxílio de Flask e extensões como Flask_SQLAlchemy, Flask_CORS, Flasgger.

A API também tem uma funcionalidade que consome dados da API externa [Open Library](https://openlibrary.org/dev/docs/api/books). É uma iniciativa sem fins lucrativos do [Internet Archive](https://archive.org/) que fornece um catálogo de informações bibliográficas abertas e de domínio público. Não são exigidos tokens, chaves ou licenças para operações de leitura.

O **banco de dados** usa SQLite. Tem duas tabelas ("livros" e "citacoes").

> **Este repositório contém apenas o *back end* da aplicação.**
> O *front end* está publicado [neste repositório](https://github.com/he-pl/citex-frontend).

## ROTAS
> A documentação completa das rotas fica disponivel via *SwaggerUI*, em http://localhost:5000/apidocs.
> (Depois que *app.py* for posto em execução).

A API de **Citex** possui atualmente as seguintes rotas:

### Lista completa de livros
> **/api/livros, GET:** recupera a lista completa de livros cadastrados

### Dados de livro específico
> **/api/livros/{id}, GET:** recupera dados de um livro cadastrado e sua lista de citações

### Buscar dados de livro na Open Library
> **/api/openlibrary/{isbn}, GET:** buscar os dados do livro via API da [Open Library](https://openlibrary.org/dev/docs/api/books), usando o ISBN digitado

### Adicionar livro
> **/api/livros, POST:** insere novo livro no banco de dados

### Adicionar citação
> **/api/citacoes, POST:** insere nova citação a um livro cadastrado

### Editar livro
> **/api/livros/{id}, PUT:** Atualiza dados de um livro existente

### Editar citação
> **/api/citacoes/{id}, PUT:** Atualiza dados de uma citação existente

### Deletar livro
> **/api/livros/{id}, DELETE:** Remove um livro e suas citações

### Deletar citação
> **/api/citacoes/{id}, DELETE:** Remove uma citação



## COMO EXECUTAR O BACKEND VIA DOCKER

**1. Necessário ter o Docker instalado.** Disponível [aqui](https://docs.docker.com/engine/install/).

**2. Clonar o repositório.** 

**3. Acesse a raiz da pasta e crie a imagem Docker.** Entre em citex-backend e use este comando:
```
docker build -t citex-backend .
```

**4. Rode o container.** Ainda em citex-backend, execute o seguinte comando:
```
  docker run -d --name flask_backend -p 5000:5000 -v "$(pwd)/data:/app/data" citex-backend
```
Depois de ativado:
- http://localhost:5000/api/livros (API JSON)
- http://localhost:5000 ou http://localhost:5000/apidocs/ (Documentação Swagger)



## COMO EXECUTAR O O APP INTEIRO VIA DOCKER

**1. Necessário ter o Docker instalado.** Disponível [aqui](https://docs.docker.com/engine/install/).

**2. Clonar este repositório e o de [front-end](https://github.com/he-pl/citex-frontend).** Salve-os na mesma pasta e mantenha os nomes dos repositorios. 

Após clonar os repositórios, o arquivo docker-compose.yml estará na pasta "citex-frontend". Para que ele funcione:
- ele deve ser ativado a partir desta pasta
- as pastas "citex-frontend" e "citex-backend" devem estar num diretório comum

**3. Acesse a raiz da pasta "citex-frontend" e rode docker-compose.** Use este comando:
```
docker-compose up --build
```
Ativados os dois containers: 
- UI do app: http://localhost:8080.
- API do backend: http://localhost:5000/api/livros
- Documentação Swagger das rotas: http://localhost:5000 ou http://localhost:5000/apidocs/
