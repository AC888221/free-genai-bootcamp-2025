# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8084 available to the world outside this container
EXPOSE 8084

# Define environment variable
ENV NAME TubeQuiz

# Run streamlit when the container launches
CMD ["streamlit", "run", "frontend/TubeQuiz.py", "--server.port=8084", "--server.address=0.0.0.0"] 