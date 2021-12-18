from database import db

class Manga(db.Model):
    id = db.Column(db.String(150), primary_key=True)
    nome = db.Column(db.String(200), unique=False, nullable=False)
    descricao = db.Column(db.String(500), unique=False, nullable=True)
    favoritado = db.relationship('Favorito',backref='manga',lazy=True)
