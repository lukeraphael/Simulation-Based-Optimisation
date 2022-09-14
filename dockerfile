FROM python:3.10-slim-buster

COPY ./parallelisation.py ./requirements.txt ./
COPY ./deploy ./deploy
RUN pip install -r requirements.txt

CMD ["python3", "parallelisation.py"]