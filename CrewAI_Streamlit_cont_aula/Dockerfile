#Define diretório code, copia requirements.tx para o container para fazer a instalação na imagem, após isso da piop install de todas essas dependências e dispara ele na porta 80

FROM python:3.12.4

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
