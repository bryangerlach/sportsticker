FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

EXPOSE 8000

# Run database migrations and start Gunicorn server
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 sportsticker.wsgi:application"]