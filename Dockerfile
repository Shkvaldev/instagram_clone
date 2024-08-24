FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY * ./

EXPOSE 3000

CMD ["fastapi", "run", "app.py", "--port", "3000"]
