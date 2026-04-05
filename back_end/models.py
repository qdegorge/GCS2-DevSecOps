from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    prenom = db.Column(db.String(50))
    nom = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) 
    role = db.Column(db.String(20), nullable=False)
    
    classe_id = db.Column(db.Integer, db.ForeignKey('classe.id'))
    classe_prof_id = db.Column(db.Integer, db.ForeignKey('classe.id'))
    
    notes = db.relationship('Note', backref='etudiant', lazy=True)
    classe_etudiant = db.relationship('Classe', foreign_keys=[classe_id], backref='eleves')
    classe_enseignee = db.relationship('Classe', foreign_keys=[classe_prof_id], backref='professeur')

class Classe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    devoirs = db.relationship('Devoir', backref='classe_concernee', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valeur = db.Column(db.Float, nullable=False)
    etudiant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    devoir_id = db.Column(db.Integer, db.ForeignKey('devoir.id'))
    devoir = db.relationship('Devoir', backref='notes')

class Devoir(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_limite = db.Column(db.DateTime) # Heure de début
    date_fin = db.Column(db.DateTime)    # Heure de fin
    professeur_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    classe_id = db.Column(db.Integer, db.ForeignKey('classe.id'))

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    expediteur_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    destinataire_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    sujet = db.Column(db.String(255), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=db.func.current_timestamp())
    lu = db.Column(db.Boolean, default=False)

    expediteur = db.relationship('User', foreign_keys=[expediteur_id], backref='messages_envoyes')
    destinataire = db.relationship('User', foreign_keys=[destinataire_id], backref='messages_recus')