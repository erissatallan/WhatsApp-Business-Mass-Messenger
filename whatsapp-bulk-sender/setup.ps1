# WhatsApp Bulk Sender - Windows Setup Script
Write-Host "🚀 Setting up WhatsApp Bulk Sender..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js 16+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Setup Backend
Write-Host "📦 Setting up Backend..." -ForegroundColor Yellow
Set-Location backend

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Blue
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Blue
& "venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
pip install -r requirements.txt

# Go back to root directory
Set-Location ..

# Setup Frontend
Write-Host "📦 Setting up Frontend..." -ForegroundColor Yellow
Set-Location frontend

# Install Node.js dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Blue
npm install

# Go back to root directory
Set-Location ..

Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Install Redis Server:"
Write-Host "   - Download from https://redis.io/download"
Write-Host "   - Or use Docker: docker run -d -p 6380:6380 redis:7-alpine --port 6380"
Write-Host "   - Or start Redis: redis-server.exe --port 6380"
Write-Host ""
Write-Host "2. Configure Twilio (Temporary WhatsApp Solution):"
Write-Host "   - Sign up at https://twilio.com and get your Account SID and Auth Token"
Write-Host "   - Enable WhatsApp Sandbox in Twilio Console"
Write-Host "   - Update .env file with your Twilio credentials:"
Write-Host "     TWILIO_ACCOUNT_SID=your_account_sid"
Write-Host "     TWILIO_AUTH_TOKEN=your_auth_token"
Write-Host ""
Write-Host "3. Configure WhatsApp Business API (Future):"
Write-Host "   - Get approved for WhatsApp Business API at business.facebook.com"
Write-Host "   - Update .env file with WABA credentials when ready"
Write-Host ""
Write-Host "4. Start the application - 4 terminals needed:" -ForegroundColor Cyan
Write-Host "   Terminal 1: redis-server.exe --port 6380"
Write-Host "   Terminal 2: cd backend; venv\Scripts\activate; python app.py"
Write-Host "   Terminal 3: cd backend; venv\Scripts\activate; celery -A celery_worker worker --loglevel=info --pool=solo"
Write-Host "   Terminal 4: cd frontend; npm start"
Write-Host ""
Write-Host "📖 For detailed instructions, see README.md"
