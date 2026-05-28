FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run collectstatic. We use dummy secret key if not set.
ENV SECRET_KEY=dummy-key-for-collectstatic
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# Script to run migrations, seed data, and start server
CMD python manage.py migrate && \
    python seed_data.py && \
    python manage.py runserver 0.0.0.0:8080
