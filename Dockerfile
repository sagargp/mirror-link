FROM python:3.7.2-stretch
MAINTAINER sagargp@gmail.com

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install --yes portaudio19-dev
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
