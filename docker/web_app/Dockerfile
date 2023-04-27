# Utilise l'image Python 3.9 comme image de base
FROM python:3.9

# Met en place le répertoire de travail
WORKDIR /app

# Copie les fichiers des exigences
COPY modules/web_app/requirements.txt .

# Installe les exigences
RUN pip install --no-cache-dir -r requirements.txt

# Copie tous les fichiers de l'application
COPY . .

# Expose le port sur lequel l'application écoutera
EXPOSE 80

# Exécute l'application

CMD ["gunicorn", "--bind", "0.0.0.0:80", "modules.web_app.app:app"]
