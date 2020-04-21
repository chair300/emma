FROM python:3.8-buster
WORKDIR /code
RUN git clone --branch v0.1 https://github.com/sverchkov/emma.git
WORKDIR /code/emma/dash-abstract-reader
RUN pip install -r requirements.txt

CMD ["python3", "cherrypy_server.py"]