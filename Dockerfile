FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories
RUN mkdir -p cards

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "collocation_bot.py"]
