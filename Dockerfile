FROM python:3.8-buster
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_ENV development
COPY dash-abstract-reader .
RUN pip install -r requirements.txt
COPY data /data
CMD ["flask", "run"]