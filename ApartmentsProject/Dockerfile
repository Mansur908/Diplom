FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONDONBUFFERED 1
WORKDIR /usr/src/project

COPY ./req.txt /usr/src/req.txt
RUN pip install -r /usr/src/req.txt
COPY . /usr/src/project

EXPOSE 8000
CMD python manage.py runserver 0.0.0.0:8000