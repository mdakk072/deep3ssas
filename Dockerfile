# Utiliser une image de base Python
FROM ultralytics/yolov5:latest-cpu
# Définir le répertoire de travail
WORKDIR /app
# Copier les fichiers de configuration et d'installation
COPY requirements.txt .
# Installer les dépendances de base et les dépendances OpenCV
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0
# Copier le reste des fichiers du projet
COPY . .
# Exposer le port 5000 pour l'application Flask
# EXPOSE 5000
# Lancer l'application
CMD ["python3", "app.py"]
