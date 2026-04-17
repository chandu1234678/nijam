# Test all backend endpoints
$baseUrl = "http://localhost:8000"

Write-Host "`n=== Testing Backend Endpoints ===" -ForegroundColor Cyan

# 1. Health Check
Write-Host "`n1. Testing /health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✓ Health: $($health.status)" -ForegroundColor Green
    Write-Host "  Model: $($health.model.model)" -ForegroundColor Gray
    Write-Host "  Accuracy: $($health.model.accuracy * 100)%" -ForegroundColor Gray
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
}

# 2. Message endpoint (without auth - should fail gracefully)
Write-Host "`n2. Testing /message (no auth)..." -ForegroundColor Yellow
try {
    $body = @{
        message = "Is the earth flat?"
        history = @()
        session_id = $null
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/message" -Method POST -ContentType "application/json" -Body $body
    Write-Host "✓ Message endpoint works" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "✓ Message endpoint requires auth (expected)" -ForegroundColor Green
    } else {
        Write-Host "✗ Message endpoint error: $_" -ForegroundColor Red
    }
}

# 3. Stats endpoint
Write-Host "`n3. Testing /stats..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/stats" -Method GET
    Write-Host "✓ Stats: Total checks = $($stats.total_checks)" -ForegroundColor Green
} catch {
    Write-Host "✗ Stats failed: $_" -ForegroundColor Red
}

# 4. Audio transcribe endpoint (should fail without file)
Write-Host "`n4. Testing /audio/transcribe..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/audio/transcribe" -Method POST
    Write-Host "✓ Audio endpoint accessible" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "✓ Audio endpoint exists (needs audio file)" -ForegroundColor Green
    } else {
        Write-Host "✗ Audio endpoint error: $_" -ForegroundColor Red
    }
}

# 5. Check OpenAPI docs
Write-Host "`n5. Testing /docs..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "$baseUrl/docs" -UseBasicParsing
    if ($docs.StatusCode -eq 200) {
        Write-Host "✓ API docs accessible at $baseUrl/docs" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Docs failed: $_" -ForegroundColor Red
}

# 6. List all routes
Write-Host "`n6. Testing /openapi.json..." -ForegroundColor Yellow
try {
    $openapi = Invoke-RestMethod -Uri "$baseUrl/openapi.json" -Method GET
    $routes = $openapi.paths.Keys | Sort-Object
    Write-Host "✓ Found $($routes.Count) API routes:" -ForegroundColor Green
    $routes | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} catch {
    Write-Host "✗ OpenAPI failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "`nBackend is running at: $baseUrl" -ForegroundColor Green
Write-Host "API Docs: $baseUrl/docs" -ForegroundColor Green
Write-Host "`nNow test the extension:" -ForegroundColor Yellow
Write-Host "1. Load extension in Chrome (chrome://extensions)" -ForegroundColor Gray
Write-Host "2. Open extension popup" -ForegroundColor Gray
Write-Host "3. Try logging in or sending a message" -ForegroundColor Gray
Write-Host "4. Check voice recorder page" -ForegroundColor Gray
