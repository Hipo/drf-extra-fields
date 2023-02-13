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

# Resolve distutils failing to import on Python 3.7
# https://github.com/pypa/get-pip/issues/124#issuecomment-1153162025
RUN apt-get install -y --reinstall python3.7-distutils

WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install tox
