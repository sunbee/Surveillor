FROM arm32v7/python:3.7.10-buster

WORKDIR /app
COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /app



