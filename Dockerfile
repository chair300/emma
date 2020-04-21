FROM python:3.8-buster
WORKDIR /code
COPY dash-abstract-reader .
RUN pip install -r requirements.txt
COPY data /data
CMD ["python3", "cherrypy_server.py"]