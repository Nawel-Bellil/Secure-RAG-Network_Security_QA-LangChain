Clear-Host

Write-Host "=====================================" -ForegroundColor Green
Write-Host "  MPLS Lab Document Test" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

$docPath = "ACTIVITÉ PRATIQUE MPLS_MPLS-TE_SDN_NFV.docx"

if (-not (Test-Path $docPath)) {
    Write-Host "`n✗ File not found: $docPath" -ForegroundColor Red
    exit
}

Write-Host "`n[1/4] Uploading Document..." -ForegroundColor Cyan
try {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $upload = Invoke-RestMethod -Uri http://localhost:8000/upload `
        -Method POST `
        -Form @{ file = Get-Item $docPath }
    $sw.Stop()
    
    Write-Host "✓ Upload Success!" -ForegroundColor Green
    Write-Host "  File: $($upload.message)" -ForegroundColor White
    Write-Host "  Chunks: $($upload.chunks_created)" -ForegroundColor Yellow
    Write-Host "  Instance: $($upload.instance_id)" -ForegroundColor White
    Write-Host "  Time: $($sw.ElapsedMilliseconds)ms" -ForegroundColor DarkGray
    Write-Host "  Security Scan:" -ForegroundColor White
    Write-Host "    - Suspicious: $($upload.security_scan.suspicious_content)" -ForegroundColor $(if ($upload.security_scan.suspicious_content) { "Red" } else { "Green" })
    Write-Host "    - Severity: $($upload.security_scan.severity)" -ForegroundColor White
    
    $chunksCreated = $upload.chunks_created
} catch {
    Write-Host "✗ Upload Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

Write-Host "`n[2/4] Asking Technical Questions..." -ForegroundColor Cyan

$questions = @(
    @{q="What is the main objective of this MPLS/MPLS-TE/SDN/NFV lab?"; short="Objective"},
    @{q="List all the configuration steps for MPLS-TE tunnels"; short="MPLS-TE Steps"},
    @{q="Explain the SDN controller setup in simple terms"; short="SDN Setup"},
    @{q="What CLI commands are needed for initial MPLS setup?"; short="CLI Commands"},
    @{q="How can I verify that MPLS tunnels are working correctly?"; short="Verification"}
)

$results = @()

foreach ($item in $questions) {
    Write-Host "`n  ❓ $($item.short)" -ForegroundColor Magenta
    
    $body = @{ question = $item.q } | ConvertTo-Json
    
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $answer = Invoke-RestMethod -Uri http://localhost:8000/ask `
            -Method POST `
            -Body $body `
            -ContentType "application/json"
        $sw.Stop()
        
        Write-Host "     Instance: $($answer.instance_id)" -ForegroundColor Yellow
        Write-Host "     Sources: $($answer.sources_count)" -ForegroundColor Cyan
        Write-Host "     Web: $($answer.web_used)" -ForegroundColor $(if ($answer.web_used) { "Green" } else { "DarkGray" })
        Write-Host "     Time: $($sw.ElapsedMilliseconds)ms" -ForegroundColor DarkGray
        Write-Host "     Security: $($answer.security_scan.severity)" -ForegroundColor White
        
        $preview = $answer.answer.Substring(0, [Math]::Min(120, $answer.answer.Length))
        Write-Host "     Preview: $preview..." -ForegroundColor White
        
        $results += @{
            question = $item.short
            answer = $answer.answer
            time = $sw.ElapsedMilliseconds
            sources = $answer.sources_count
            web_used = $answer.web_used
        }
        
    } catch {
        Write-Host "     ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 300
}

Write-Host "`n[3/4] Database Stats..." -ForegroundColor Cyan
try {
    $stats = Invoke-RestMethod -Uri http://localhost:8000/stats
    Write-Host "✓ Stats Retrieved" -ForegroundColor Green
    Write-Host "  Total Chunks: $($stats.total_chunks)" -ForegroundColor Yellow
    Write-Host "  Status: $($stats.status)" -ForegroundColor White
} catch {
    Write-Host "✗ Stats Failed" -ForegroundColor Red
}

Write-Host "`n[4/4] Full Answers..." -ForegroundColor Cyan
foreach ($result in $results) {
    Write-Host "`n$("=" * 60)" -ForegroundColor DarkGray
    Write-Host "Q: $($result.question)" -ForegroundColor Magenta
    Write-Host "$("=" * 60)" -ForegroundColor DarkGray
    Write-Host $result.answer -ForegroundColor White
    Write-Host "`nMetadata: Sources=$($result.sources) | Web=$($result.web_used) | Time=$($result.time)ms" -ForegroundColor DarkGray
}

Write-Host "`n=====================================" -ForegroundColor Green
Write-Host "  Test Complete!" -ForegroundColor Green
Write-Host "  Chunks Created: $chunksCreated" -ForegroundColor Yellow
Write-Host "  Questions Answered: $($results.Count)" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Green