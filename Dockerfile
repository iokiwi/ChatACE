FROM python:alpine

COPY requirements.txt requirements.txt
COPY main.py main.py

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
# CMD ["python", "main.py"]
