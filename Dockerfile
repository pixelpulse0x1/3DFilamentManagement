FROM python:3.10-alpine

WORKDIR /app

RUN apk add --no-cache tzdata

ENV TZ=Asia/Shanghai

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY modules/ ./modules/
COPY static/ ./static/
COPY templates/ ./templates/
COPY entrypoint.sh /

RUN chmod +x /entrypoint.sh

EXPOSE 3155

ENTRYPOINT ["/entrypoint.sh"]
