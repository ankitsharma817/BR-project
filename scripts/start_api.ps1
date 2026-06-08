# Windows PowerShell: Run migrations then start API
$env:PYTHONPATH = (Get-Location).Path

Write-Host "Running Alembic migrations..."
alembic upgrade head

Write-Host "Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
