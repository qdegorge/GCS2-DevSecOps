from app import app, db, bcrypt  
from models import User, Classe 

def init():
    with app.app_context():
        db.drop_all()
        db.create_all()

        ma_classe = Classe(nom="B1 Guardia")
        db.session.add(ma_classe)
        db.session.commit()

        users_to_create = [
            {"username": "Momo Farton", "pwd": "1234!", "role": "admin", "prenom": "Momo", "nom": "Farton", "email": "momo@guardia.local"},
            {"username": "Ayoub Ayouzi", "pwd": "jesuisadmin!", "role": "admin", "prenom": "Ayoub", "nom": "Ayouzi", "email": "ayoub@guardia.local"},
            {"username": "Bassem Neuille", "pwd": "IEDZIHFUEFB387", "role": "professeur", "prenom": "Bassem", "nom": "Neuille", "email": "bassem@guardia.local"},
            {"username": "Mattieu Blanche", "pwd": "1234!", "role": "etudiant", "prenom": "Mattieu", "nom": "Blanche", "email": "mattieu@guardia.local"},
            {"username": "Pierre Abril", "pwd": "1234!", "role": "etudiant", "prenom": "Pierre", "nom": "Abril", "email": "pierre@guardia.local"},
        ]

        for u in users_to_create:
            h_pwd = bcrypt.generate_password_hash(u['pwd']).decode('utf-8')
            
            new_user = User(
                username=u['username'],
                password_hash=h_pwd,  
                role=u['role'],
                prenom=u['prenom'],
                nom=u['nom'],
                email=u['email']     
            )

            if u['role'] == "etudiant":
                new_user.classe_id = ma_classe.id 
            elif u['role'] == "professeur":
                new_user.classe_prof_id = ma_classe.id 

            db.session.add(new_user)
        
        db.session.commit()
        print("--- Base de données initialisée avec succès ! ---")

if __name__ == "__main__":
    init()