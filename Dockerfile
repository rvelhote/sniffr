FROM ubuntu:trusty

RUN sed -i 's/http:\/\/archive/http:\/\/pt\.archive/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get -y install python-pip python-dev python-openssl python-requests python-flask && \
    pip install flask-assets

EXPOSE 5000
ENTRYPOINT ["python", "/opt/workspace/sniffr.py"]
