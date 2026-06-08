# Windows PowerShell: Start Celery workers (separate terminals recommended)
$env:PYTHONPATH = (Get-Location).Path

Write-Host "Starting matching worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "celery -A api.tasks.celery_app worker --queues=matching --concurrency=2 --loglevel=info --hostname=matching@%h"

Write-Host "Starting embedding worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "celery -A api.tasks.celery_app worker --queues=embedding --concurrency=1 --loglevel=info --hostname=embedding@%h"

Write-Host "Starting email+webhook worker..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "celery -A api.tasks.celery_app worker --queues=email,webhooks --concurrency=4 --loglevel=info --hostname=misc@%h"

Write-Host "Starting Flower on http://localhost:5555 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
  "celery -A api.tasks.celery_app flower --port=5555"

Write-Host "All workers launched in separate windows."
