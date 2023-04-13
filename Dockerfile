FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y mesa-utils && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install django-cors-headers && \
    pip install psycopg2-binary
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:9000"]