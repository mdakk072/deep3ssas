# Utilise l'image Python 3.9 comme image de base
FROM python:3.9

# Met en place le répertoire de travail
WORKDIR /app

# Copie les fichiers des exigences
COPY ./modules/data_handler/requirements.txt .

# Installe les exigences
RUN pip install --no-cache-dir -r requirements.txt

# Copie les fichiers de l'application
COPY ./modules/data_handler /app/modules/data_handler
COPY ./static /app/modules/data_handler/static


# Copie les fichiers à la racine du projet (sans les dossiers)
COPY ./*.txt /app/
COPY ./*.json /app/
# Expose le port sur lequel l'application écoutera
EXPOSE 80

# Exécute l'application

CMD ["python",  "modules/data_handler/app.py"]
#CMD ["gunicorn", "--bind", "0.0.0.0:80", "modules.data_handler.app:app"]
