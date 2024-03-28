FROM python:3.10.0

COPY . /server

WORKDIR /server

RUN pip install -r requirements.txt

# VOLUME ["/server/app"]

EXPOSE 8000

CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000", "--reload"]

