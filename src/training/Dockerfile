FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir pandas==3.0.6 prophet==1.5.0 'statsmodels>=0.14,<1' 'psycopg[binary]>=3.2,<4'
COPY worker.py .
CMD ["python","worker.py"]
