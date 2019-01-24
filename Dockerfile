FROM ubuntu:16.04

MAINTAINER Marco Chiappetta <lambdacomplete@gmail.com>

# Needed to be able to install python versions.
RUN apt-get update && apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y \
	python3.4 \
	python3.5 \
	python3.6 \
	gdal-bin \
	python-pip

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install tox
