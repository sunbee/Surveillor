FROM arm32v7/python:3.7.10-buster

ENV READTHEDOCS=True

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install matplotlib==3.0.2

COPY . /app
RUN pip install /app/Assets/tflite_runtime-1.14.0-cp37-cp37m-linux_armv7l.whl

CMD ["python3", "/app/sentry_dev.py"]


