from database import db

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), unique=False, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    senha = db.Column(db.String(80), unique=False, nullable=False)
    favoritos = db.relationship('Favorito',backref='usuario',lazy=True)