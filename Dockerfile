FROM i386/ubuntu:14.04

RUN apt-get update && \
        apt-get install -y python python-numpy python-opencv && \
        apt-get clean -y
ADD pynaoqi-python2.7-2.1.4.13-linux32.tar.gz /opt
ENV PYTHONPATH="${PYTHONPATH}:/opt/pynaoqi-python2.7-2.1.4.13-linux32"
