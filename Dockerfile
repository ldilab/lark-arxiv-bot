# syntax=docker/dockerfile:1

FROM python:3.10-alpine

ENV TZ="Asia/Seoul"
RUN date

RUN apk add build-base linux-headers
RUN apk add --no-cache gcc

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN pip uninstall pycrypto
RUN pip install pycryptodome


WORKDIR /app

EXPOSE 5000

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]