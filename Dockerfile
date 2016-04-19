FROM ubuntu

MAINTAINER Marco Chiappetta <lambdacomplete@gmail.com>

WORKDIR /drf-extra-fields

RUN apt-get update && apt-get install -y \
	git \
	python2.7 \
	python-dev \
	build-essential \
	postgresql \
	python-pip \
	postgresql-server-dev-9.3 \
	zlib1g-dev \
	libjpeg8-dev \
	libgeos-dev

RUN git clone https://github.com/Hipo/drf-extra-fields.git .

RUN pip install -r requirements.txt

RUN pip install tox

CMD ["cd", "/drf-extra-fields"]