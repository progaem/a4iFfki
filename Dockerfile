FROM python:3.11-slim
WORKDIR /a4iFfki
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /a4iFfki/src
CMD ["python", "main.py"]