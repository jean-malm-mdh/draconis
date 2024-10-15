FROM python:3.11

EXPOSE 8000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Putting some generic font file
ENV DRACONIS_FONT="/app/fonts/AdventPro-Regular.ttf"

WORKDIR /app/Web_GUI

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
