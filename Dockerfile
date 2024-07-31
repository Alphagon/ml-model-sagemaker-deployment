FROM python:3.9.13

WORKDIR /app

COPY requirements/core.txt /app/requirements/core.txt
RUN pip install --no-cache-dir -r requirements/core.txt

COPY requirements/dev.txt /app/requirements/dev.txt
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY requirements/api.txt /app/requirements/api.txt
RUN pip install --no-cache-dir -r requirements/api.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]