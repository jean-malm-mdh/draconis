FROM python:3.11

WORKDIR /app
# git clone --recurse-submodules https://github.com/jean-malm-mdh/draconis.git
# WORKDIR /app/draconis

# Putting some generic font file
ENV DRACONIS_FONT="/app/fonts/AdventPro-Regular.ttf"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

COPY . .

WORKDIR /app/Web_GUI

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
