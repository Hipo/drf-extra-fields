FROM ubuntu:18.04

MAINTAINER Marco Chiappetta <lambdacomplete@gmail.com>

# Needed to be able to install python versions.
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update && apt-get install -y \
	python3.5 \
	python3.6 \
	python3.7 \
	python3.8 \
	gdal-bin \
	python3-pip

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install tox
