FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

# ENV user=my_user
# ENV password=123
# ENV host=db
# ENV port=3306
# ENV database="my_db"

COPY . . 
