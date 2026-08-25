FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /tmp/noiop /data
ENV NOIOP_DB_PATH=/tmp/noiop/noiop.db
EXPOSE 8080
CMD ["gunicorn","-b","0.0.0.0:8080","--workers","1","--threads","4","--timeout","120","app:app"]
