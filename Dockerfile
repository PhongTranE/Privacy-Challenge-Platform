FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5050

# Run Flask on the correct port
CMD ["flask", "run", "--host=0.0.0.0", "--port=5050"]