# WhatsApp Bulk Sender - Complete Setup Guide

## 🎯 What You'll Build

A professional bulk WhatsApp messaging system that can:
- Send personalized messages to thousands of contacts
- Upload contact lists via Excel files
- Monitor campaigns in real-time
- Handle rate limiting and retries automatically
- Maintain WhatsApp compliance

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8+** - Download from https://python.org
- [ ] **Node.js 16+** - Download from https://nodejs.org  
- [ ] **Redis Server** - See installation options below
- [ ] **WhatsApp Business Account** - For API access
- [ ] **Meta Business Account** - Verified business account

## 🔧 Step-by-Step Installation

### Step 1: Install Redis Server

Choose one option:

#### Option A: Windows Native Installation
1. Download Redis from https://github.com/microsoftarchive/redis/releases
2. Extract and run `redis-server.exe`

#### Option B: Docker (Recommended)
```powershell
# Pull and run Redis container
docker run -d --name redis-whatsapp -p 6379:6379 redis:7-alpine

# Verify it's running
docker ps
```

#### Option C: WSL (Windows Subsystem for Linux)
```bash
# In WSL terminal
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### Step 2: Clone/Setup Project

The project structure is already created in your workspace:
```
whatsapp-bulk-sender/
├── backend/           # Flask API + Celery
├── frontend/          # React application  
├── docker-compose.yml # Docker setup
├── setup.ps1         # Windows setup script
└── README.md         # Documentation
```

### Step 3: Automated Setup (Recommended)

Run the automated setup script:

```powershell
# Navigate to project directory
cd "c:\Users\USER PC\Work\Business Automations\Mwihaki Intimates\whatsapp-bulk-sender"

# Run setup script
.\setup.ps1
```

### Step 4: Manual Setup (Alternative)

If automated setup fails:

#### Backend Setup:
```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment  
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Frontend Setup:
```powershell
# Navigate to frontend
cd frontend

# Install Node.js dependencies
npm install
```

### Step 5: WhatsApp Business API Configuration

#### 5.1 Apply for API Access
1. Go to https://business.facebook.com
2. Create/verify your business account
3. Navigate to "WhatsApp Business API"
4. Submit application with required documents
5. Wait for approval (typically 1-4 weeks)

#### 5.2 Get API Credentials
Once approved, you'll receive:
- **Phone Number ID** (e.g., `123456789012345`)
- **Access Token** (long string starting with `EAA...`)

#### 5.3 Update Code Configuration
Edit these files and replace `YOUR_PHONE_NUMBER_ID`:

**File: backend/app.py** (Line ~244)
```python
# Change this line:
url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"

# To your actual Phone Number ID:
url = "https://graph.facebook.com/v17.0/123456789012345/messages"
```

**File: backend/celery_worker.py** (Line ~153)
```python
# Change this line:
url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"

# To your actual Phone Number ID:
url = "https://graph.facebook.com/v17.0/123456789012345/messages"
```

## 🚀 Running the Application

You need **4 terminals** running simultaneously:

### Terminal 1: Redis Server
```powershell
# If installed natively:
redis-server

# If using Docker:
docker start redis-whatsapp
```

### Terminal 2: Flask Backend
```powershell
cd backend
venv\Scripts\activate
python app.py
```
**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Terminal 3: Celery Worker
```powershell
cd backend  
venv\Scripts\activate
celery -A celery_worker worker --loglevel=info
```
**Expected output:**
```
[2024-08-03 10:30:15] [INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-08-03 10:30:15] [INFO/MainProcess] celery@COMPUTER ready.
```

### Terminal 4: React Frontend
```powershell
cd frontend
npm start
```
**Expected output:**
```
Compiled successfully!
Local:            http://localhost:3000
```

## 🎮 Using the Application

### 1. Access the Application
Open your browser and go to: **http://localhost:3000**

### 2. Prepare Your Excel File
Create an Excel file (.xlsx) with these columns:

| phone | name | last_product | location |
|-------|------|--------------|----------|
| 0712345678 | John Doe | iPhone 14 | Nairobi |
| +254723456789 | Jane Smith | MacBook Pro | Mombasa |
| 254734567890 | Bob Wilson | AirPods | Kisumu |

**Required columns:** `phone`, `name`
**Optional columns:** Any additional fields for personalization

### 3. Create a Campaign
1. Click "Upload & Configure" tab
2. Enter campaign name
3. Enter your WhatsApp API key (Access Token)
4. Upload your Excel file
5. Set rate limit (start with 2 seconds)
6. Write your message template:

```
Hi {name}! 

Thanks for your interest in our products. 

Based on your location in {location}, we have special offers available.

Visit our store: https://yourstore.com

Reply STOP to unsubscribe.
```

7. Click "Start Campaign"

### 4. Monitor Progress
1. Switch to "Monitor Campaigns" tab
2. View real-time statistics:
   - Total messages
   - Sent count
   - Delivered count
   - Failed count
   - Progress percentage

## ⚠️ Important Compliance Notes

### WhatsApp Business API Rules:
- ✅ Only message customers who opted in
- ✅ Include opt-out instructions ("Reply STOP")
- ✅ Keep content relevant and valuable
- ✅ Respect rate limits (start slow)
- ✅ Monitor delivery rates

### Recommended Rate Limits:
- **< 100 contacts:** 2-3 seconds between messages
- **100-1000 contacts:** 1-2 seconds between messages  
- **1000+ contacts:** 1 second (monitor carefully)

## 🐛 Troubleshooting

### Common Issues:

#### 1. Redis Connection Error
```
redis.exceptions.ConnectionError: Error 10061
```
**Solution:** Make sure Redis server is running

#### 2. Celery Import Error
```
ImportError: cannot import name 'process_campaign_task'
```
**Solution:** Make sure you're in the correct directory and virtual environment is activated

#### 3. WhatsApp API Error 401
```
Invalid API key
```
**Solution:** 
- Check your Access Token
- Ensure Phone Number ID is correctly configured
- Verify your WhatsApp Business API is approved

#### 4. Excel Upload Error
```
Missing required columns: ['phone', 'name']
```
**Solution:** Ensure your Excel file has columns named exactly 'phone' and 'name'

#### 5. Frontend Not Loading
```
Cannot connect to backend
```
**Solution:**
- Ensure Flask backend is running on port 5000
- Check console for CORS errors
- Verify proxy setting in package.json

## 📊 Testing Strategy

### Phase 1: Small Test (5-10 contacts)
1. Create a test Excel file with 5 contacts
2. Use a simple message template
3. Set rate limit to 3 seconds
4. Monitor delivery success

### Phase 2: Medium Test (50-100 contacts)
1. Expand to 50 contacts
2. Reduce rate limit to 2 seconds
3. Test personalization variables
4. Monitor for any failures

### Phase 3: Production (1000+ contacts)
1. Use full contact list
2. Optimize rate limit based on test results
3. Monitor delivery rates closely
4. Be ready to pause if issues arise

## 🔄 Production Deployment

For production deployment:

1. **Use Docker Compose:**
```powershell
docker-compose up -d
```

2. **Environment Variables:**
- Copy `.env.example` to `.env`
- Fill in production values
- Never commit API keys to version control

3. **Monitoring:**
- Set up log monitoring
- Configure delivery receipt webhooks
- Monitor rate limit compliance

## 📞 Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review the console output in all terminals
3. Test with a small dataset first
4. Ensure WhatsApp API credentials are correct

## 🎯 Next Steps

1. **Start with testing** using 5-10 contacts
2. **Monitor delivery rates** and adjust rate limits
3. **Scale gradually** to larger contact lists
4. **Set up proper logging** for production use
5. **Consider webhook integration** for delivery receipts

Good luck with your WhatsApp bulk messaging system! 🚀
