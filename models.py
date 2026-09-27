from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


# Garante que o SQLite respeite as constraints de FOREIGN KEY.
# Por padrão o SQLite ignora ForeignKey, permitindo citações "órfãs"
# apontando para livro_id inexistentes. Isso ativa a checagem real.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Livro(db.Model):
    __tablename__ = 'livros'

    livro_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ISBN = db.Column(db.String(20))
    livro_titulo = db.Column(db.String(255), nullable=False)
    livro_subtitulo = db.Column(db.String(255))
    livro_autor = db.Column(db.String(255))
    livro_editora = db.Column(db.String(100))
    livro_anopublic = db.Column(db.Integer)
    livro_localpublic = db.Column(db.String(100))
    livro_comentario = db.Column(db.Text)

    citacoes = db.relationship('Citacao', backref='livro', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'livro_id': self.livro_id,
            'ISBN': self.ISBN,
            'livro_titulo': self.livro_titulo,
            'livro_subtitulo': self.livro_subtitulo,
            'livro_autor': self.livro_autor,
            'livro_editora': self.livro_editora,
            'livro_anopublic': self.livro_anopublic,
            'livro_localpublic': self.livro_localpublic,
            'livro_comentario': self.livro_comentario
        }


class Citacao(db.Model):
    __tablename__ = 'citacoes'

    citacao_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.livro_id'), nullable=False)
    pagina_inicial = db.Column(db.String(20))
    pagina_final = db.Column(db.String(20))
    texto_citacao = db.Column(db.Text, nullable=False)
    comentario = db.Column(db.Text)

    def to_dict(self):
        return {
            'citacao_id': self.citacao_id,
            'livro_id': self.livro_id,
            'pagina_inicial': self.pagina_inicial,
            'pagina_final': self.pagina_final,
            'texto_citacao': self.texto_citacao,
            'comentario': self.comentario
        }
