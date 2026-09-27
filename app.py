from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flasgger import Swagger
from models import db, Livro, Citacao
import requests
import os

app = Flask(__name__)
CORS(app)

# Configuração SQLite
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'database.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Configuração e personalização do Swagger UI
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "API - Gerenciamento de Fichamento Acadêmico",
        "description": "API RESTful para cadastro de livros, gerenciamento de citações acadêmicas e integração com a API de ISBN da Open Library.",
        "version": "1.0.0"
    },
    "tags": [
        {"name": "Livros", "description": "Endpoints para gestão da biblioteca do usuário"},
        {"name": "Citações", "description": "Endpoints para gestão de citações e notas relativas a um livro"},
        {"name": "Integrações (Open Library)", "description": "Consultas a APIs bibliográficas externas"}
    ]
}

Swagger(app, config=swagger_config, template=swagger_template)

with app.app_context():
    db.create_all()


# --- HELPER PARA EXTRAÇÃO HISTÓRICA DO PRIMEIRO LOCAL DE PUBLICAÇÃO ---

def get_historical_first_place(info):
    """
    Tenta encontrar o local de publicação da edição mais antiga registrada para esta obra.
    Caso não encontre, retorna o primeiro local listado para a edição específica.
    """
    places = info.get('publish_places', [])
    default_place = places[0] if places and isinstance(places[0], str) else (
        places[0].get('name', '') if places and isinstance(places[0], dict) else ""
    )

    works = info.get('works', [])
    if not works:
        return default_place

    work_key = works[0].get('key')  # Ex: "/works/OL45883W"
    if not work_key:
        return default_place

    try:
        editions_res = requests.get(f"https://openlibrary.org{work_key}/editions.json", timeout=5)
        if editions_res.status_code != 200:
            return default_place

        editions = editions_res.json().get('entries', [])

        valid_editions = [
            e for e in editions
            if e.get('publish_date') and e.get('publish_places')
        ]

        if not valid_editions:
            return default_place

        def extract_year(edition):
            date_str = str(edition.get('publish_date', ''))
            digits = ''.join(filter(str.isdigit, date_str))
            return int(digits[-4:]) if len(digits) >= 4 else 9999

        sorted_editions = sorted(valid_editions, key=extract_year)
        earliest_places = sorted_editions[0]['publish_places']

        if earliest_places:
            first_place = earliest_places[0]
            if isinstance(first_place, dict):
                return first_place.get('name', default_place)
            return str(first_place)

    except requests.exceptions.RequestException:
        pass
    except Exception:
        pass

    return default_place


# --- ROTAS DA API ---

# ===== ROTA RAIZ =====
@app.route('/')
def index():
    """Redireciona a raiz da API para a documentação Swagger."""
    return redirect('/apidocs/')

# ===== GRUPO: LIVROS =====

@app.route('/api/livros', methods=['GET'])
def get_livros():
    """Busca todos os livros cadastrados.
    ---
    tags:
      - Livros
    responses:
      200:
        description: Lista de todos os livros cadastrados no sistema.
    """
    livros = Livro.query.all()
    return jsonify([livro.to_dict() for livro in livros])


@app.route('/api/livros/<int:id>', methods=['GET'])
def get_livro(id):
    """Busca os dados de um livro específico e suas citações associadas.
    ---
    tags:
      - Livros
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID único do livro
        example: 1
    responses:
      200:
        description: Ficha do livro acompanhada de suas citações.
      404:
        description: Livro não localizado.
    """
    livro = Livro.query.get_or_404(id)
    dados = livro.to_dict()
    dados['citacoes'] = [c.to_dict() for c in livro.citacoes]
    return jsonify(dados)


@app.route('/api/livros', methods=['POST'])
def add_livro():
    """Cadastra um novo livro no acervo.
    ---
    tags:
      - Livros
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - livro_titulo
          properties:
            ISBN: {type: string, example: "9788535902778"}
            livro_titulo: {type: string, example: "Dom Casmurro"}
            livro_subtitulo: {type: string, example: ""}
            livro_autor: {type: string, example: "Machado de Assis"}
            livro_editora: {type: string, example: "Companhia das Letras"}
            livro_anopublic: {type: integer, example: 2019}
            livro_localpublic: {type: string, example: "São Paulo"}
            livro_comentario: {type: string, example: "Edição comemorativa."}
    responses:
      201:
        description: Livro adicionado com sucesso.
      400:
        description: Dados inválidos ou campo obrigatório ausente.
    """
    data = request.get_json(silent=True) or {}

    livro_titulo = (data.get('livro_titulo') or '').strip()
    if not livro_titulo:
        return jsonify({'error': 'O campo livro_titulo é obrigatório'}), 400

    novo_livro = Livro(
        ISBN=data.get('ISBN'),
        livro_titulo=livro_titulo,
        livro_subtitulo=data.get('livro_subtitulo'),
        livro_autor=data.get('livro_autor'),
        livro_editora=data.get('livro_editora'),
        livro_anopublic=data.get('livro_anopublic'),
        livro_localpublic=data.get('livro_localpublic'),
        livro_comentario=data.get('livro_comentario')
    )
    db.session.add(novo_livro)
    db.session.commit()
    return jsonify(novo_livro.to_dict()), 201


@app.route('/api/livros/<int:id>', methods=['PUT'])
def update_livro(id):
    """Atualiza as informações bibliográficas de um livro existente.
    ---
    tags:
      - Livros
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID único do livro a ser editado
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            ISBN: {type: string, example: "9788535902778"}
            livro_titulo: {type: string, example: "Dom Casmurro (Edição Revisada)"}
            livro_subtitulo: {type: string, example: ""}
            livro_autor: {type: string, example: "Machado de Assis"}
            livro_editora: {type: string, example: "Companhia das Letras"}
            livro_anopublic: {type: integer, example: 2021}
            livro_localpublic: {type: string, example: "São Paulo"}
            livro_comentario: {type: string, example: "Atualizado comentários."}
    responses:
      200:
        description: Dados do livro atualizados com sucesso.
      400:
        description: Dados inválidos.
      404:
        description: Livro não localizado.
    """
    livro = Livro.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    if 'livro_titulo' in data and not (data.get('livro_titulo') or '').strip():
        return jsonify({'error': 'O campo livro_titulo não pode ficar vazio'}), 400

    livro.ISBN = data.get('ISBN', livro.ISBN)
    livro.livro_titulo = data.get('livro_titulo', livro.livro_titulo)
    livro.livro_subtitulo = data.get('livro_subtitulo', livro.livro_subtitulo)
    livro.livro_autor = data.get('livro_autor', livro.livro_autor)
    livro.livro_editora = data.get('livro_editora', livro.livro_editora)
    livro.livro_anopublic = data.get('livro_anopublic', livro.livro_anopublic)
    livro.livro_localpublic = data.get('livro_localpublic', livro.livro_localpublic)
    livro.livro_comentario = data.get('livro_comentario', livro.livro_comentario)

    db.session.commit()
    return jsonify(livro.to_dict())


@app.route('/api/livros/<int:id>', methods=['DELETE'])
def delete_livro(id):
    """Remove um livro e todas as suas citações em cascata.
    ---
    tags:
      - Livros
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID único do livro a ser excluído
        example: 1
    responses:
      200:
        description: Livro e citações removidos com sucesso.
      404:
        description: Livro não localizado.
    """
    livro = Livro.query.get_or_404(id)
    db.session.delete(livro)
    db.session.commit()
    return jsonify({'message': 'Livro deletado com sucesso'})


# ===== GRUPO: CITAÇÕES =====

@app.route('/api/citacoes', methods=['POST'])
def add_citacao():
    """Adiciona uma nova citação a um livro existente.
    ---
    tags:
      - Citações
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - livro_id
            - texto_citacao
          properties:
            livro_id: {type: integer, example: 1}
            pagina_inicial: {type: string, example: "42"}
            pagina_final: {type: string, example: "43"}
            texto_citacao: {type: string, example: "Mudemos de assunto. Tu não és capaz de entender isto."}
            comentario: {type: string, example: "Trecho chave referente à narração não confiável de Bentinho."}
    responses:
      201:
        description: Citação gravada com sucesso.
      400:
        description: Dados inválidos ou campo obrigatório ausente.
      404:
        description: livro_id informado não existe.
    """
    data = request.get_json(silent=True) or {}

    livro_id = data.get('livro_id')
    texto_citacao = (data.get('texto_citacao') or '').strip()

    if livro_id is None:
        return jsonify({'error': 'O campo livro_id é obrigatório'}), 400
    if not texto_citacao:
        return jsonify({'error': 'O campo texto_citacao é obrigatório'}), 400

    # Garante que o livro referenciado realmente existe antes de criar a citação
    if not Livro.query.get(livro_id):
        return jsonify({'error': f'Nenhum livro encontrado com livro_id={livro_id}'}), 404

    nova_citacao = Citacao(
        livro_id=livro_id,
        pagina_inicial=data.get('pagina_inicial'),
        pagina_final=data.get('pagina_final'),
        texto_citacao=texto_citacao,
        comentario=data.get('comentario')
    )
    db.session.add(nova_citacao)
    db.session.commit()
    return jsonify(nova_citacao.to_dict()), 201


@app.route('/api/citacoes/<int:id>', methods=['PUT'])
def update_citacao(id):
    """Atualiza o texto, paginação ou notas de uma citação.
    ---
    tags:
      - Citações
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID da citação a ser atualizada
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            pagina_inicial: {type: string, example: "42"}
            pagina_final: {type: string, example: "44"}
            texto_citacao: {type: string, example: "Mudemos de assunto. Tu não és capaz de entender isto..."}
            comentario: {type: string, example: "Comentário revisado."}
    responses:
      200:
        description: Citação alterada com sucesso.
      400:
        description: Dados inválidos.
      404:
        description: Citação não localizada.
    """
    citacao = Citacao.query.get_or_404(id)
    data = request.get_json(silent=True) or {}

    if 'texto_citacao' in data and not (data.get('texto_citacao') or '').strip():
        return jsonify({'error': 'O campo texto_citacao não pode ficar vazio'}), 400

    citacao.pagina_inicial = data.get('pagina_inicial', citacao.pagina_inicial)
    citacao.pagina_final = data.get('pagina_final', citacao.pagina_final)
    citacao.texto_citacao = data.get('texto_citacao', citacao.texto_citacao)
    citacao.comentario = data.get('comentario', citacao.comentario)

    db.session.commit()
    return jsonify(citacao.to_dict())


@app.route('/api/citacoes/<int:id>', methods=['DELETE'])
def delete_citacao(id):
    """Exclui uma citação do sistema.
    ---
    tags:
      - Citações
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID da citação a ser deletada
        example: 1
    responses:
      200:
        description: Citação removida com sucesso.
      404:
        description: Citação não localizada.
    """
    citacao = Citacao.query.get_or_404(id)
    db.session.delete(citacao)
    db.session.commit()
    return jsonify({'message': 'Citação deletada com sucesso'})


# ===== GRUPO: INTEGRAÇÕES (OPEN LIBRARY) =====

@app.route('/api/openlibrary/<isbn>', methods=['GET'])
def search_open_library(isbn):
    """Busca os metadados de um livro via API de ISBN da Open Library.
    ---
    tags:
      - Integrações (Open Library)
    parameters:
      - name: isbn
        in: path
        type: string
        required: true
        description: Número ISBN de 10 ou 13 dígitos sem hífens
        example: "9788535902778"
    responses:
      200:
        description: Dados bibliográficos auto-preenchidos.
      404:
        description: Livro não localizado na Open Library.
      502:
        description: Falha de comunicação com a Open Library.
    """
    clean_isbn = isbn.replace('-', '').strip()
    url = f"https://openlibrary.org/isbn/{clean_isbn}.json"

    try:
        res = requests.get(url, timeout=5)
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Não foi possível conectar à Open Library'}), 502

    if res.status_code == 404:
        return jsonify({'error': 'Livro não encontrado na Open Library'}), 404
    elif res.status_code != 200:
        return jsonify({'error': 'Erro ao consultar a Open Library'}), res.status_code

    info = res.json()

    # 1. Título e Subtítulo
    titulo = info.get('title', '')
    subtitulo = info.get('subtitle', '')

    # 2. Resolução dos nomes dos Autores
    autores_list = []
    for author_ref in info.get('authors', []):
        author_key = author_ref.get('key')
        if author_key:
            try:
                author_res = requests.get(f"https://openlibrary.org{author_key}.json", timeout=3)
                if author_res.status_code == 200:
                    autores_list.append(author_res.json().get('name', ''))
            except requests.exceptions.RequestException:
                pass
    autores = ", ".join(filter(None, autores_list))

    # 3. Editora
    publishers = info.get('publishers', [])
    editoras = ", ".join(publishers) if isinstance(publishers, list) else str(publishers)

    # 4. Ano de Publicação
    pub_date = info.get('publish_date', '')
    digits = ''.join(filter(str.isdigit, pub_date))
    ano = int(digits[-4:]) if len(digits) >= 4 else None

    # 5. Local de Publicação (Histórico da 1ª Edição)
    local_publicacao = get_historical_first_place(info)

    return jsonify({
        'ISBN': clean_isbn,
        'livro_titulo': titulo,
        'livro_subtitulo': subtitulo,
        'livro_autor': autores,
        'livro_editora': editoras,
        'livro_anopublic': ano,
        'livro_localpublic': local_publicacao
    })


if __name__ == '__main__':
    # FLASK_DEBUG=1 liga o debugger/reloader do Werkzeug para desenvolvimento local.
    # Nunca deixe isso ligado em um ambiente exposto publicamente (RCE via debugger).
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
