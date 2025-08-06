# WhatsApp Bulk Sender

A comprehensive system for sending bulk WhatsApp Business messages to thousands of contacts with Excel file upload, message personalization, and real-time monitoring.

## 🚀 Features

- **Excel File Upload**: Upload contact lists with phone numbers, names, and custom fields
- **Message Personalization**: Use variables like `{name}`, `{last_product}` in templates
- **Rate Limiting**: Intelligent rate limiting to avoid WhatsApp blocks
- **Real-time Monitoring**: Track campaign progress with live updates
- **Retry Logic**: Automatic retry for failed messages with exponential backoff
- **Campaign Management**: Create, monitor, and manage multiple campaigns with pagination (20 per page)
- **Reply Collection**: Collect and analyze WhatsApp replies with advanced filtering and pagination
- **AI-Powered Analysis**: Gemini AI sentiment analysis and intelligent auto-responses
- **Search & Pagination**: Efficient browsing of large datasets with 20 items per page
- **WhatsApp Compliance**: Built-in compliance features to respect WhatsApp's terms

## 🏗️ Architecture

```
Frontend (React) → Backend API (Flask) → Celery Workers → WhatsApp API
                                    ↓
                               Redis Queue
                                    ↓
                            Message Status DB (SQLite)
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Redis Server** (for task queue)
- **WhatsApp Business API Access** (Meta Business verification required)

## 🛠️ Installation & Setup

### 1. Quick Setup Script

```powershell
# Run the automated setup script (Windows PowerShell)
.\setup.ps1
```

### 2. Configure Messaging API

#### Option A: Twilio WhatsApp API (Immediate Testing)

1. **Sign up for Twilio**: https://twilio.com
2. **Get your credentials**: Account SID and Auth Token from Console
3. **Enable WhatsApp Sandbox**: 
   - Go to Console > Messaging > Try it out > Send a WhatsApp message
   - Follow the sandbox setup instructions
   - Note your sandbox number (usually starts with +1 415...)

4. **Update .env file**:
```env
# Twilio Configuration (Current - for immediate testing)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# WhatsApp Business API (Future - when approved)
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN=your_whatsapp_business_api_token_here
```

5. **Test Twilio connection**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python test_twilio.py
```

#### Option B: WhatsApp Business API (Future)

1. **Apply for WhatsApp Business API**: https://business.facebook.com
2. **Complete Meta Business verification** (can take several weeks)
3. **Get your Phone Number ID and Access Token**
4. **Update .env file** with your WABA credentials
5. **Switch API in code** (instructions in Migration section below)

### 2. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

## 🚀 Running the Application

You need to run 4 components in separate terminals:

### Terminal 1: Start Redis
```powershell
# Start Redis on port 6380 (configured for this project)
redis-server.exe --port 6380

# Or with Docker
docker run -d -p 6380:6380 redis:7-alpine redis-server --port 6380
```

### Terminal 2: Start Flask Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python app.py
```

### Terminal 3: Start Celery Worker
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

### Terminal 4: Start React Frontend
```powershell
cd frontend
npm start
```

## 📱 Using the Application

### 1. Prepare Your Excel File

Create an Excel file (.xlsx) with columns:
- `phone` (required) - Format: +1234567890 or +254712345678
- `first_name`, `last_name`, `company` (optional)
- Any other custom fields for personalization

Example:
| phone | first_name | company |
|-------|------------|---------|
| +1234567890 | John | Acme Corp |
| +254712345678 | Jane | Tech Inc |

### 2. Create a Campaign

1. Open http://localhost:3000 in your browser
2. Go to "Upload Contacts" tab
3. Upload your Excel file
4. Write your message template with placeholders:
   ```
   Hi {first_name}! 
   
   We have a special offer for {company}.
   Check out our latest collections at Mwihaki Intimates.
   
   Best regards,
   The Mwihaki Team
   ```
5. Set your rate limit (start with 5-10 messages per minute for Twilio sandbox)
6. Click "Start Campaign"

### 3. Monitor Your Campaign

- Switch to "Monitor Campaigns" tab
- View real-time progress and delivery status
- Check success/failure counts and error messages

### Terminal 3: Start Celery Worker
```powershell
cd backend
venv\Scripts\activate
celery -A celery_worker worker --loglevel=info
```

### Terminal 4: Start React Frontend
```powershell
cd frontend
npm start
```

The application will be available at: **http://localhost:3000**

## 📊 Excel File Format

Your Excel file should contain these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `phone` | ✅ | Phone numbers (any format) |
| `name` | ✅ | Customer names |
| `last_product` | ❌ | For personalization |
| `location` | ❌ | Custom field |
| *any other columns* | ❌ | Will be available for personalization |

### Example Excel File:
```
phone          | name        | last_product | location
0712345678     | John Doe    | iPhone 14    | Nairobi
+254723456789  | Jane Smith  | MacBook Pro  | Mombasa
254734567890   | Bob Wilson  | AirPods      | Kisumu
```

## 📝 Message Template Examples

```
Hi {name}! 

Thanks for purchasing {last_product} from our store. 

We have a special 20% discount for customers in {location}.

Use code: SAVE20

Visit our store: https://yourstore.com

Reply STOP to unsubscribe.
```

## ⚙️ WhatsApp Business API Setup

### 1. Get API Access
1. Go to https://business.facebook.com
2. Create/verify your business account
3. Apply for WhatsApp Business API access
4. Wait for approval (can take weeks)

### 2. Configure API Endpoint
In both `app.py` and `celery_worker.py`, replace:
```python
url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"
```

With your actual Phone Number ID:
```python
url = "https://graph.facebook.com/v17.0/123456789012345/messages"
```

### 3. API Key
- Use your WhatsApp Business API **Access Token** as the API key in the frontend
- Keep this secure and never commit it to version control

## 📈 Rate Limiting Guidelines

| Contacts | Recommended Rate | Notes |
|----------|------------------|-------|
| < 100 | 2 seconds | Conservative start |
| 100-1000 | 1-2 seconds | Monitor delivery rates |
| 1000+ | 1 second | Adjust based on success rate |

⚠️ **Always start conservative** and increase speed based on delivery success rates.

## 🔒 Compliance Checklist

- ✅ Always include opt-out instructions ("Reply STOP to unsubscribe")
- ✅ Only message customers who have opted in
- ✅ Respect rate limits to avoid being blocked
- ✅ Monitor delivery rates and adjust accordingly
- ✅ Keep message content relevant and valuable
- ✅ Handle failed messages gracefully

## 🐛 Troubleshooting

### Common Issues:

1. **Redis Connection Error**
   ```
   ConnectionError: Error 10061 connecting to localhost:6379
   ```
   **Solution**: Make sure Redis server is running

2. **Celery Worker Not Starting**
   ```
   ImportError: cannot import name 'soft_time_limit'
   ```
   **Solution**: Update Celery: `pip install celery==5.3.4`

3. **Excel File Upload Error**
   ```
   Missing required columns: ['phone', 'name']
   ```
   **Solution**: Ensure your Excel file has 'phone' and 'name' columns

4. **WhatsApp API Error 401**
   ```
   Invalid API key
   ```
   **Solution**: Check your API key and Phone Number ID

### Debug Mode:

To run in debug mode with detailed logging:
```powershell
# Backend
cd backend
set FLASK_DEBUG=1
python app.py

# Celery Worker
celery -A celery_worker worker --loglevel=debug
```

## 📚 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/start-campaign` | Start a new campaign |
| GET | `/api/campaigns` | Get all campaigns |
| GET | `/api/campaign-status/<id>` | Get campaign status |

## 🎯 Next Steps

1. **Test with small dataset** (5-10 contacts)
2. **Monitor rate limits** and delivery success
3. **Set up proper logging** for production
4. **Configure webhook** for delivery receipts (advanced)
5. **Add authentication** for production deployment

## 📄 License

This project is for educational and business use. Ensure compliance with WhatsApp's Business API terms of service.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review WhatsApp Business API documentation
3. Test with small contact lists first
