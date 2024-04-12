FROM python:3.10

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug", "--bind", "0.0.0.0:9000", "foodgram_backend.wsgi:application"]
