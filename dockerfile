FROM python:3.10-slim-buster

COPY ./parallelisation.py ./requirements.txt ./
COPY ./deploy ./deploy
RUN pip install -r requirements.txt

CMD ["python3", "parallelisation.py", "--n_gen", "1", "--workers", "1", "--pop_size", "1", "--choice", "kubernetes"]