# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8083 available to the world outside this container
EXPOSE 8083

# Define environment variable
ENV NAME SongWords

# Run streamlit when the container launches
CMD ["streamlit", "run", "SongWords.py", "--server.port=8083", "--server.address=0.0.0.0"] 