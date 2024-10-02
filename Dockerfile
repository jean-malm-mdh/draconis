FROM python:3.11


# Putting some generic font file
ENV DRACONIS_FONT="/app/draconis/fonts/AdventPro-Regular.ttf"

EXPOSE 8000

WORKDIR /app
RUN git clone --recursive https://github.com/jean-malm-mdh/draconis.git

WORKDIR /app/draconis

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/draconis/draconis_parser

RUN chmod +x regen_parser.sh
RUN ./regen_parser.sh

# COPY . .

WORKDIR /app/draconis/Web_GUI

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
