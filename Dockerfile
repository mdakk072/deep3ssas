# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Flask and requests packages
RUN pip install Flask requests

# Copy the rest of the application's code into the container
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Install gunicorn
RUN pip install gunicorn

# Run the command to start the Flask app using Gunicorn
CMD gunicorn --bind 0.0.0.0:80 app:app
