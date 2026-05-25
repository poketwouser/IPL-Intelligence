FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Set default port
ENV PORT=8050
EXPOSE $PORT

# Run the application using shell form to evaluate the $PORT variable
CMD gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120
