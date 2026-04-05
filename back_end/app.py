import os
from datetime import datetime, timedelta
import datetime as dt_module
from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt 
from flask_wtf.csrf import CSRFProtect
from models import db, User, Classe, Note, Devoir, Message
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from markupsafe import escape

app = Flask(__name__, 
            template_folder='../front_end/templates', 
            static_folder='../front_end/static')

# Configuration de la base de données et sécurité
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/Intranet'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'caca'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True  
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' 
app.config['SESSION_COOKIE_SECURE'] = True

# Gestion des Logs
if not os.path.exists('logs'):
    os.mkdir('logs')
    
file_handler = RotatingFileHandler('logs/secops.log', maxBytes=102400, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s | IP: %(remote_addr)s', 
    defaults={'remote_addr': 'N/A'} 
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Initialisation des extensions
db.init_app(app)
bcrypt = Bcrypt(app) 
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Décorateur de protection par rôle
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                user_info = current_user.username if current_user.is_authenticated else "Visiteur Anonyme"  
                app.logger.warning(f"ALERTE SÉCURITÉ (403) : {user_info} a tenté d'accéder à {request.path}")
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'    
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data:;"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# --- ROUTES AUTHENTIFICATION ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_propre = request.form.get('username', '').strip()
        password_clair = request.form.get('password')
        
        try:
            user = User.query.filter_by(username=username_propre).first()
        except Exception as e:
            app.logger.error(f"ERREUR DB : {e}")
            flash('Erreur interne du serveur.')
            return render_template('login.html')

        if user and bcrypt.check_password_hash(user.password_hash, password_clair):
            login_user(user)
            session.permanent = True 
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects')
    return render_template('login.html')

# --- ROUTE DASHBOARD PRINCIPALE ---

@app.route('/dashboard')
@login_required
def dashboard():  
    devoirs = []
    eleves = []
    classe_nom = ""
    toutes_classes = []
    professeurs = []
    
    if current_user.role == 'etudiant':
        devoirs = Devoir.query.filter_by(classe_id=current_user.classe_id).all()
        classe_nom = current_user.classe_etudiant.nom if current_user.classe_etudiant else "N/A"

    elif current_user.role == 'admin':
        toutes_classes = Classe.query.all()
        for c in toutes_classes:
            c.eleves_filtres = [u for u in c.eleves if u.role == 'etudiant']
            c.profs_filtres = [u for u in c.eleves if u.role == 'professeur']
            
        professeurs = User.query.filter_by(role='professeur').all()
    
    elif current_user.role == 'professeur':
        if current_user.classe_prof_id:
            eleves = User.query.filter_by(classe_id=current_user.classe_prof_id).all()
            classe_nom = current_user.classe_enseignee.nom if current_user.classe_enseignee else "N/A"
        else:
            eleves = User.query.filter_by(role='etudiant').all()
            classe_nom = "Toutes les classes"
        devoirs = Devoir.query.filter_by(professeur_id=current_user.id).all()
        
        # Calcul des moyennes pour l'onglet enseignant
        for e in eleves:
            notes = [n.valeur for n in e.notes]
            e.moyenne = round(sum(notes)/len(notes), 2) if notes else "Aucune note"

    elif current_user.role == 'admin':
        toutes_classes = Classe.query.all()
        professeurs = User.query.filter_by(role='professeur').all()

    return render_template('dashboard.html', devoirs=devoirs, eleves=eleves, classe=classe_nom, toutes_classes=toutes_classes, professeurs=professeurs)

# --- ROUTES GESTION NOTES ET DEVOIRS ---

@app.route('/ajouter_note', methods=['POST'])
@login_required
@role_required('professeur', 'admin')
def ajouter_note():
    try:
        valeur = float(request.form.get('valeur'))
        if 0 <= valeur <= 20:
            db.session.add(Note(valeur=valeur, etudiant_id=request.form.get('etudiant_id'), devoir_id=request.form.get('devoir_id')))
            db.session.commit()
            flash("Note attribuée avec succès !", "success")
        else:
            flash("La note doit être entre 0 et 20.", "danger")
    except:
        flash("Format de note invalide.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/modifier_note/<int:note_id>', methods=['POST'])
@login_required
@role_required('professeur', 'admin')  
def modifier_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        valeur = float(request.form.get('valeur'))
        if 0 <= valeur <= 20:
            note.valeur = valeur
            db.session.commit()
            flash('Note mise à jour !', 'success')
        else:
            flash("La note doit être entre 0 et 20.", "danger")
    except:
        flash("Format invalide.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/ajouter_devoir', methods=['POST'])
@login_required
@role_required('professeur', 'admin') 
def ajouter_devoir():
    try:
        titre = request.form.get('titre')
        date_jour = request.form.get('date_limite') 
        h_debut = request.form.get('heure_debut')  
        h_fin = request.form.get('heure_fin')      
        classe_id = request.form.get('classe_id')

        print(f"DEBUG: {date_jour} de {h_debut} à {h_fin}")

        if not all([titre, date_jour, h_debut, h_fin, classe_id]):
            flash("Tous les champs sont obligatoires !", "warning")
            return redirect(url_for('dashboard'))

        debut_dt = datetime.strptime(f"{date_jour} {h_debut}", '%Y-%m-%d %H:%M')
        fin_dt = datetime.strptime(f"{date_jour} {h_fin}", '%Y-%m-%d %H:%M')

        nouveau_devoir = Devoir(
            titre=titre,
            date_limite=debut_dt,
            date_fin=fin_dt,
            professeur_id=current_user.id,
            classe_id=int(classe_id)
        )

        db.session.add(nouveau_devoir)
        db.session.commit()
        flash('Évaluation ajoutée avec succès !', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR SQLALCHEMY : {e}") 
        flash(f"Erreur lors de l'ajout : {str(e)}", "danger")

    return redirect(url_for('dashboard'))

# --- ROUTES ADMINISTRATION ---

@app.route('/admin/creer_classe', methods=['POST'])
@login_required
@role_required('admin')
def creer_classe():
    nom = request.form.get('nom')
    if nom:
        db.session.add(Classe(nom=nom))
        db.session.commit()
        flash(f'La classe {nom} a été créée !', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/affecter_prof', methods=['POST'])
@login_required
@role_required('admin')
def affecter_prof():
    prof_id = request.form.get('prof_id')
    classe_id = request.form.get('classe_id')
    if prof_id:
        prof = User.query.get(prof_id)
        if prof:
            prof.classe_id = classe_id if classe_id else None
            db.session.commit()
            nom_classe = Classe.query.get(classe_id).nom if classe_id else "Aucune"
            flash(f"Le professeur {prof.prenom} {prof.nom} a été affecté à la classe : {nom_classe}", "success")
    return redirect(url_for('dashboard'))

@app.route('/admin/utilisateurs')
@login_required
@role_required('admin')
def gestion_utilisateurs():
    utilisateurs = User.query.all()
    classes = Classe.query.all()
    return render_template('gestion_users.html', utilisateurs=utilisateurs, classes=classes)

@app.route('/admin/modifier_user_classe/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def modifier_user_classe(user_id):
    user = User.query.get_or_404(user_id)
    nouvelle_classe_id = request.form.get('classe_id')
    user.classe_id = nouvelle_classe_id if nouvelle_classe_id else None
    db.session.commit()
    flash(f"Classe mise à jour pour {user.username}", "success")
    return redirect(url_for('gestion_utilisateurs'))

@app.route('/creer_utilisateur', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def creer_utilisateur():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        prenom = request.form.get('prenom')
        nom = request.form.get('nom')
        role = request.form.get('role')
        classe_id = request.form.get('classe_id')

        if role in ['professeur', 'admin']:
            classe_id = None
        elif not classe_id or classe_id == "":
            classe_id = None

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return redirect(url_for('creer_utilisateur'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        email_auto = f"{prenom.lower()}.{nom.lower()}@ecole.fr"
        
        nouvel_utilisateur = User(
            username=username,
            password_hash=hashed_pw,
            prenom=prenom,
            nom=nom,
            email=email_auto, 
            role=role,
            classe_id=classe_id
        )

        try:
            db.session.add(nouvel_utilisateur)
            db.session.commit()
            flash(f"Utilisateur {prenom} {nom} créé avec succès !", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"ERREUR SQL : {e}") 
            flash("Erreur lors de l'enregistrement. Vérifiez que l'email n'existe pas déjà.", "danger")

    classes = Classe.query.all()
    return render_template('creer_utilisateur.html', classes=classes)

@app.route('/api/data/<category>')
@login_required
def get_data(category):
    data = []
    
    if category == 'emploi':
        # 1. On détermine quelle classe on veut afficher
        classe_id = None
        if current_user.role == 'etudiant':
            classe_id = current_user.classe_id
        elif current_user.role == 'professeur':
            classe_id = current_user.classe_prof_id 
        
        # 2. On récupère les devoirs
        if current_user.role == 'admin':
            devoirs = Devoir.query.all()
        elif classe_id:
            devoirs = Devoir.query.filter_by(classe_id=classe_id).all()
        else:
            devoirs = Devoir.query.filter_by(professeur_id=current_user.id).all()
            
        for d in devoirs:
            if d.date_limite:
           
                prof = User.query.get(d.professeur_id)
                if prof:
                    nom_prof = f"{prof.prenom} {prof.nom}"
                else:
                    nom_prof = "Professeur inconnu"
        
                debut = d.date_limite
                fin = d.date_fin if d.date_fin else (debut + timedelta(hours=1))
        
                data.append({
                    'titre': d.titre,
                    'debut': debut.isoformat(),
                    'fin': fin.isoformat(),
                    'salle': nom_prof, 
                    'is_devoir': True
                })
                
    elif category == 'profil':
        nom_classe = 'N/A'
        if current_user.role == 'etudiant' and current_user.classe_etudiant:
            nom_classe = current_user.classe_etudiant.nom
        elif current_user.role == 'professeur' and hasattr(current_user, 'classe_enseignee') and current_user.classe_enseignee:
            nom_classe = current_user.classe_enseignee.nom

        data = {
            'nom': current_user.nom, 
            'prenom': current_user.prenom, 
            'email': getattr(current_user, 'email', 'N/A'), 
            'classe': nom_classe, 
            'statut': current_user.role
        }
        
    elif category == 'messagerie':
        messages = Message.query.filter_by(destinataire_id=current_user.id).order_by(Message.date_envoi.desc()).all()
        data = [{
            'id': m.id, 
            'sujet': m.sujet, 
            'contenu': m.contenu, 
            'date_envoi': m.date_envoi.strftime('%d/%m %H:%M') if m.date_envoi else "N/A", 
            'expediteur_nom': m.expediteur.nom if m.expediteur else "?", 
            'prenom': m.expediteur.prenom if m.expediteur else ""
        } for m in messages]
        
    elif category == 'notes':
        if current_user.role == 'etudiant':
            data = [{'matiere': n.devoir.titre, 'note': n.valeur} for n in Note.query.filter_by(etudiant_id=current_user.id).all() if n.devoir]
            
    return jsonify(data)

@app.route('/api/users')
@login_required
def get_users():
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify([{'id': u.id, 'nom': u.nom, 'prenom': u.prenom, 'role': u.role.capitalize()} for u in users])

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Aucune donnée reçue'}), 400

        destinataire_id = data.get('destinataire_id')
        sujet = data.get('sujet', '').strip()
        contenu = data.get('contenu', '').strip()

        if not destinataire_id or not contenu:
            return jsonify({'success': False, 'message': 'Champs obligatoires manquants'}), 400

        nouveau_msg = Message(
            expediteur_id=current_user.id,
            destinataire_id=int(destinataire_id), 
            sujet=sujet,
            contenu=contenu
        )
        
        db.session.add(nouveau_msg)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Message envoyé !'})
    
    except Exception as e:
        db.session.rollback()
        print(f"ERREUR CRITIQUE MESSAGERIE : {str(e)}") 
        return jsonify({'success': False, 'message': "Erreur lors de l'enregistrement en base."}), 500
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(port=5050, debug=True)