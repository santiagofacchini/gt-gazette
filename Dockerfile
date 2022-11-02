FROM python:3.12.0a1-alpine3.16

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "/usr/src/app/gt-gazette.py" ]
