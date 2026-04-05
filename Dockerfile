# Utiliser une image Python officielle et légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du code source
COPY . .

# Exposer le port utilisé par Flask
EXPOSE 5050

# Commande pour lancer l'application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5050"]