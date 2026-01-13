# Quick Setup Script for Windows
# This script sets up log-filter Docker environment on Windows

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  log-filter Docker Setup for Windows" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found!" -ForegroundColor Red
    Write-Host "  Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "Checking if Docker is running..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and run this script again" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setting up directories..." -ForegroundColor Yellow

# Create required directories
$directories = @("output", "config", "test-logs")
foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "✓ Directory exists: $dir" -ForegroundColor Green
    } else {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    }
}

# Create sample log file if test-logs is empty
$testLogsPath = "test-logs"
$logFiles = Get-ChildItem -Path $testLogsPath -Filter "*.log" -ErrorAction SilentlyContinue

if ($logFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "Creating sample log files..." -ForegroundColor Yellow

    $sampleLog = @"
2026-01-13 10:00:00 INFO Application started successfully
2026-01-13 10:01:23 ERROR Database connection failed: Connection timeout after 30s
2026-01-13 10:02:15 WARNING Cache miss for key: user_123
2026-01-13 10:03:45 ERROR Failed to process request: timeout occurred
2026-01-13 10:04:12 INFO Request processed successfully in 145ms
2026-01-13 10:05:33 CRITICAL System overload detected - CPU at 98%
2026-01-13 10:06:00 ERROR Database query failed: syntax error in SQL statement
2026-01-13 10:07:15 INFO Background job completed successfully
2026-01-13 10:08:22 WARNING High memory usage: 85% of available RAM
2026-01-13 10:09:10 ERROR Failed to connect to external API: network unreachable
"@

    $sampleLog | Out-File -FilePath "$testLogsPath\app.log" -Encoding UTF8
    Write-Host "✓ Created: test-logs\app.log" -ForegroundColor Green

    $systemLog = @"
2026-01-13 09:00:00 INFO System boot completed in 23s
2026-01-13 09:30:00 WARNING High memory usage detected: 85%
2026-01-13 10:00:00 ERROR Failed to start service: nginx (port already in use)
2026-01-13 10:15:00 INFO Service nginx started successfully on port 8080
2026-01-13 11:00:00 CRITICAL Disk space critically low: 95% used on /dev/sda1
2026-01-13 11:30:00 WARNING SSL certificate expires in 7 days
"@

    $systemLog | Out-File -FilePath "$testLogsPath\system.log" -Encoding UTF8
    Write-Host "✓ Created: test-logs\system.log" -ForegroundColor Green
} else {
    Write-Host "✓ Test log files already exist ($($logFiles.Count) files)" -ForegroundColor Green
}

# Check if config file exists
if (-not (Test-Path "config\local.yaml")) {
    Write-Host ""
    Write-Host "Note: config\local.yaml should already exist from the repository" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Building Docker images..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes on first run)" -ForegroundColor Gray
Write-Host ""

# Build production image
Write-Host "Building production image (log-filter:latest)..." -ForegroundColor Cyan
try {
    docker build -t log-filter:latest . 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Production image built successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to build production image" -ForegroundColor Red
        Write-Host "  Run manually: docker build -t log-filter:latest ." -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Error building production image: $_" -ForegroundColor Red
}

# Build development image
Write-Host "Building development image (log-filter:dev)..." -ForegroundColor Cyan
try {
    docker-compose -f docker-compose.dev.yml build 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Development image built successfully" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to build development image" -ForegroundColor Red
        Write-Host "  Run manually: docker-compose -f docker-compose.dev.yml build" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Error building development image: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Start Commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Run basic filter:" -ForegroundColor White
Write-Host "   docker-compose -f docker-compose.local.yml run --rm log-filter-local" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Search for specific errors:" -ForegroundColor White
Write-Host "   docker run --rm -v `${PWD}/test-logs:/logs:ro -v `${PWD}/output:/output log-filter:latest ERROR /logs -o /output/errors.txt --stats" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Development mode (live reload):" -ForegroundColor White
Write-Host "   docker-compose -f docker-compose.dev.yml run --rm log-filter-dev ERROR /logs" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  • Quick Reference: .github\docs\DOCKER_QUICKREF_WINDOWS.md" -ForegroundColor Gray
Write-Host "  • Complete Guide:  .github\docs\analize\docker-local-setup-analysis.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Happy filtering! 🔍" -ForegroundColor Cyan
