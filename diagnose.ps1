Write-Host "`n=== DIAGNOSTIC COMPLET ===`n" -ForegroundColor Cyan

# 1. Docker Desktop Status
Write-Host "1. Docker Desktop Status:" -ForegroundColor Yellow
try {
    docker version
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is NOT running!" -ForegroundColor Red
    Write-Host "→ Start Docker Desktop and wait 60 seconds" -ForegroundColor Yellow
    exit
}

# 2. Container Status
Write-Host "`n2. Container Status:" -ForegroundColor Yellow
docker-compose ps

# 3. Detailed Container Info
Write-Host "`n3. All Docker Containers:" -ForegroundColor Yellow
docker ps -a

# 4. Logs from Each App
Write-Host "`n4. App Logs (Last 10 Lines Each):" -ForegroundColor Yellow

Write-Host "`n--- App Instance 1 ---" -ForegroundColor Cyan
docker logs --tail 10 rag_app_instance_1 2>&1

Write-Host "`n--- App Instance 2 ---" -ForegroundColor Cyan
docker logs --tail 10 rag_app_instance_2 2>&1

Write-Host "`n--- App Instance 3 ---" -ForegroundColor Cyan
docker logs --tail 10 rag_app_instance_3 2>&1

Write-Host "`n--- Nginx ---" -ForegroundColor Cyan
docker logs --tail 10 nginx_load_balancer 2>&1

# 5. Network Status
Write-Host "`n5. Docker Network:" -ForegroundColor Yellow
docker network ls | Select-String "langchain"

# 6. Port Listening Check
Write-Host "`n6. Ports Listening:" -ForegroundColor Yellow
netstat -an | Select-String "8001|8002|8003|8080" | Select-String "LISTENING"

# 7. Docker Compose Config
Write-Host "`n7. Docker Compose Config Check:" -ForegroundColor Yellow
docker-compose config --quiet
if ($?) {
    Write-Host "✓ docker-compose.yml is valid" -ForegroundColor Green
} else {
    Write-Host "✗ docker-compose.yml has errors!" -ForegroundColor Red
}

Write-Host "`n=== DIAGNOSTIC COMPLETE ===`n" -ForegroundColor Cyan