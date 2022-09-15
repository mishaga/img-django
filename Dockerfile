FROM python:3.10

RUN mkdir -p /project/uploads/originals && mkdir /project/uploads/resizes && mkdir /project/src
WORKDIR /project/src

COPY ./img /project/src
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
