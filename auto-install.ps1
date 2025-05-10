# MiniWare Installation Script
# This script installs all dependencies required for MiniWare using Chocolatey

# Function to check if a command exists
function Test-CommandExists {
    param ($command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $command) { return $true }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

# Function to check if a directory exists
function Test-DirectoryExists {
    param ($path)
    return Test-Path -Path $path -PathType Container
}

# Set execution policy to allow script execution
Write-Host "Setting execution policy to allow script execution..." -ForegroundColor Yellow
try {
    # Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
} catch {
    Write-Host "Failed to set execution policy. You may need to run this script as administrator." -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Check if Chocolatey is installed, if not install it
if (-not (Test-CommandExists choco)) {
    Write-Host "Chocolatey is not installed. Installing Chocolatey..." -ForegroundColor Yellow
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    } catch {
        Write-Host "Failed to install Chocolatey. Please install it manually from https://chocolatey.org/install" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Chocolatey is already installed." -ForegroundColor Green
}

# Refresh environment variables after Chocolatey installation
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Install Python 3.12.6
if (-not (Test-CommandExists python) -or -not (python --version 2>&1 | Select-String -Pattern "3.12.6")) {
    Write-Host "Installing Python 3.12.6..." -ForegroundColor Yellow
    choco install python --version=3.12.6 -y
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "Python 3.12.6 is already installed." -ForegroundColor Green
}

# Install Node.js
if (-not (Test-CommandExists node)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    choco install nodejs -y
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "Node.js is already installed." -ForegroundColor Green
}

# Install Git
if (-not (Test-CommandExists git)) {
    Write-Host "Installing Git..." -ForegroundColor Yellow
    choco install git -y
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "Git is already installed." -ForegroundColor Green
}

# Install FFmpeg
if (-not (Test-CommandExists ffmpeg)) {
    Write-Host "Installing FFmpeg..." -ForegroundColor Yellow
    choco install ffmpeg -y
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "FFmpeg is already installed." -ForegroundColor Green
}

# Clone the repository if it doesn't exist
$repoPath = Join-Path $PSScriptRoot "miniware"
if (-not (Test-DirectoryExists $repoPath)) {
    Write-Host "Cloning MiniWare repository..." -ForegroundColor Yellow
    git clone https://github.com/doggphin/miniware.git $repoPath
} else {
    Write-Host "MiniWare repository already exists." -ForegroundColor Green
}

# Navigate to the repository directory
Set-Location $repoPath

# Set up Python virtual environment and install requirements
Write-Host "Setting up Python virtual environment and installing requirements..." -ForegroundColor Yellow
$apiPath = Join-Path $repoPath "api"
$venvPath = Join-Path $apiPath "venv"

if (-not (Test-DirectoryExists $venvPath)) {
    Set-Location $apiPath
    python -m venv venv
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Activate the virtual environment and install requirements
Set-Location $apiPath
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $activateScript
pip install -r requirements.txt
# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Install Node.js dependencies for the frontend
Write-Host "Installing Node.js dependencies for the frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $repoPath "frontend"
Set-Location $frontendPath
npm install
# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Return to the repository root
Set-Location $repoPath
# Final refresh of environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "`nMiniWare installation completed successfully!" -ForegroundColor Green
Write-Host "`nTo start MiniWare, run:" -ForegroundColor Cyan
Write-Host "  - start.bat (if using Command Prompt)" -ForegroundColor Cyan
Write-Host "  - or execute the following commands in PowerShell:" -ForegroundColor Cyan
Write-Host "    1. Start-Process cmd -ArgumentList '/k', 'cd api && call venv\Scripts\activate.bat && python manage.py runserver'" -ForegroundColor Cyan
Write-Host "    2. Start-Process cmd -ArgumentList '/k', 'cd frontend && npm run dev'" -ForegroundColor Cyan
Write-Host "    3. Start-Sleep -Seconds 10" -ForegroundColor Cyan
Write-Host "    4. Start-Process http://localhost:5173/corr" -ForegroundColor Cyan

# Keep the window open until the user presses a key
Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
