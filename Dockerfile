FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY get_cookies_from_supabase_keys.py .
CMD ["python", "get_cookies_from_supabase_keys.py"]