FROM python:3.12-slim

# Evita que Python genere archivos .pyc (.pyc bytecode)
ENV PYTHONDONTWRITEBYTECODE=1

# Deshabilita el buffering de salida para ver los logs en tiempo real en Docker
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el contenido
COPY . .

# Por razones de seguridad, creamos y usamos un usuario que no sea root
RUN adduser -u 5678 --disabled-password --gecos "" wisphub && chown -R wisphub /app
USER wisphub

# Exponemos el puerto
EXPOSE 8000

# Añadimos un Health Check para que Docker sepa si la API se bloqueó
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Iniciamos Gunicorn con Uvicorn Workers para ambiente de Producción
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
