GCS2-UE7-2 DEVSECOPS - Plateforme de Gestion Académique Sécurisée 🛡️

Ce projet est une application web de gestion académique (notes, classes, emplois du temps) conçue avec une approche **DevSecOps** complète. Il a été réalisé dans le cadre de l'UE7-2 à Guardia Cybersecurity School.

## 🚀 Fonctionnalités & RBAC
L'application implémente un contrôle d'accès strict basé sur les rôles (RBAC):
- **Administrateur** : Gestion des utilisateurs, des classes et des emplois du temps.
- **Professeur** : Création de devoirs, attribution de notes et consultation de son emploi du temps.
- **Étudiant** : Consultation de ses propres notes et de son emploi du temps personnel.

## 🛡️ Mesures de Sécurité Appliquées
- **Hachage des mots de passe** : Utilisation de bcrypt.
- **Protection CSRF** : Tokens obligatoires sur tous les formulaires.
- **Sécurisation SQL** : Utilisation exclusive de requêtes paramétrées via SQLAlchemy (pas de concaténation).
- **Validation des entrées** : Assainissement des données pour prévenir les injections.
- **Pipeline CI/CD** : Analyses de sécurité automatisées via GitHub Actions.

## 🛠️ Stack Technique
- **Back-end** : Python / Flask.
- **Base de données** : MySQL.
- **Conteneurisation** : Docker & Docker Compose.
- **CI/CD** : GitHub Actions (Flake8, pip-audit, SonarCloud, OWASP ZAP).

## 📦 Installation et Lancement
L'application est entièrement conteneurisée. Pour la lancer en une commande :

1. Assurez-vous d'avoir **Docker** et **Docker Compose** installés.
2. Clonez le dépôt.
3. À la racine, lancez la commande :
   ```bash
   docker-compose up --build
