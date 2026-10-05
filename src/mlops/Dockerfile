FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pandas==3.0.6
COPY pipeline.py .
CMD ["python","pipeline.py"]
