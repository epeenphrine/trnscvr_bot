FROM python:3.8

WORKDIR /app
COPY . /app

RUN pip install pipenv 
RUN pipenv install -r requirements.txt
CMD pipenv run python options_chain_req.py 