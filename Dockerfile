FROM resin/rpi-raspbian:jessie

RUN apt-get update \
    && apt-get install -y \
        python3 \
        python3-pip \
        build-essential \
        python3-dev \
        zlib1g-dev \
        libjpeg-dev \
        wget \
    && pip3 install --upgrade pip \
    && pip install --upgrade setuptools 

