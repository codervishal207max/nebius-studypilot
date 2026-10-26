FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x start.sh
ENV DB_PATH=/srv/data/assistant.db
EXPOSE 8501
CMD ["./start.sh"]