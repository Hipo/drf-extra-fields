FROM ubuntu:latest

# Needed to be able to install python versions.
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y \
	python3.7 \
	python3.8 \
	python3.9 \
	python3.10 \
	gdal-bin \
	python3-pip

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install tox
