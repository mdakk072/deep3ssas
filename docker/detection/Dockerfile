FROM ultralytics/yolov5:latest-cpu
# Définir le répertoire de travail
WORKDIR /app
# Copier les fichiers de configuration et d'installation
COPY requirements.txt .
# Installer les dépendances de base et les dépendances OpenCV
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn && \
    apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0
# Copier le reste des fichiers du projet
COPY . .
# Exposer le port 80 pour l'application Flask
EXPOSE 80
# Lancer l'application avec Gunicorn en mode production
CMD gunicorn --bind 0.0.0.0:5000 app:app
