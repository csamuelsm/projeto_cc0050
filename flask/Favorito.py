from database import db

class Favorito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer,db.ForeignKey('usuario.id'))
    id_manga = db.Column(db.String(150),db.ForeignKey('manga.id'))