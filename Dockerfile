FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["gunicorn", "stockproj.wsgi:application", "--bind", "0.0.0.0:8000"]