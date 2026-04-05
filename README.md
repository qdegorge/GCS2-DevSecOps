# GCS2-UE7-2 DEVSECOPS - Plateforme de Gestion Académique Sécurisée 🛡️

Ce projet est une application web de gestion académique (notes, classes, emplois du temps) conçue avec une approche **DevSecOps** complète. Il a été réalisé dans le cadre de l'UE7-2 à la **Guardia Cybersecurity School**.

## 🚀 Fonctionnalités & RBAC
L'application implémente un contrôle d'accès strict basé sur les rôles (RBAC) :
- **Administrateur** : Gestion des utilisateurs, des classes et des emplois du temps.
- **Professeur** : Création de devoirs, attribution de notes et consultation de son emploi du temps.
- **Étudiant** : Consultation de ses propres notes et de son emploi du temps personnel (cloisonnement strict).

## 🛡️ Mesures de Sécurité Appliquées
- **Hachage des mots de passe** : Utilisation de `bcrypt`.
- **Protection CSRF** : Tokens obligatoires sur tous les formulaires.
- **Sécurisation SQL** : Utilisation exclusive de requêtes paramétrées via SQLAlchemy.
- **Gestion des sessions** : Cookies sécurisés avec attributs HttpOnly et SameSite.
- **Pipeline CI/CD** : Analyses de sécurité automatisées (SAST/DAST via SonarCloud, Flake8, pip-audit et OWASP ZAP) sur GitHub Actions.

## 🛠️ Stack Technique
- **Back-end** : Python / Flask.
- **Base de données** : MySQL.
- **Conteneurisation** : Docker & Docker Compose.

---

## 📦 Installation et Lancement (Pour l'Audit de la Semaine 2)

L'application est entièrement conteneurisée. Voici la procédure exacte pour la lancer depuis zéro :

**1. Lancer les conteneurs (Serveur + Base de données)**
Ouvrez un terminal à la racine du projet et tapez :
```bash
docker-compose up --build
```
Attendez que le terminal affiche Running on http://0.0.0.0:5050.

Initialiser la Base de données (Création des tables et comptes)
Laissez le premier terminal tourner. Ouvrez un nouveau terminal (toujours à la racine du projet) et exécutez le script d'initialisation à l'intérieur du conteneur :

Bash
docker exec -it secops_flask python init.py
(Si une erreur de fichier introuvable survient, essayez : docker exec -it secops_flask python back_end/init.py)

Accéder à l'application
Ouvrez votre navigateur et allez sur : 👉 http://localhost:5050

🔑 Comptes de Test
voici les comptes générés par défaut :

Admin : Username Momo Farton  / Mot de passe : 1234!

Professeur : Username Bassem Neuille  / Mot de passe : IEDZIHFUEFB387

Étudiant : Username Mattieu Blanche  / Mot de passe : 1234!
