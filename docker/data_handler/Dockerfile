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
# Set environment variables
ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV APIHOSTNAME=${APIHOSTNAME}
ENV AZURE_CONNECTION_STRING=${AZURE_CONNECTION_STRING}
ENV CONTAINER_NAME_IMAGES=${CONTAINER_NAME_IMAGES}
ENV CONTAINER_NAME_LABELS=${CONTAINER_NAME_LABELS}
# Expose le port sur lequel l'application écoutera
EXPOSE 80
# Exécute l'application
CMD ["python",  "modules/data_handler/app.py"]
