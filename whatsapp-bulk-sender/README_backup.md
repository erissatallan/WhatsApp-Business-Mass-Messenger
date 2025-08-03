# WhatsApp Bulk Sender

A comprehensive system for sending bulk WhatsApp Business messages to thousands of contacts with Excel file upload, message personalization, and real-time monitoring.

## 🚀 Features

- **Excel File Upload**: Upload contact lists with phone numbers, names, and custom fields
- **Message Personalization**: Use variables like `{name}`, `{last_product}` in templates
- **Rate Limiting**: Intelligent rate limiting to avoid WhatsApp blocks
- **Real-time Monitoring**: Track campaign progress with live updates
- **Retry Logic**: Automatic retry for failed messages with exponential backoff
- **Campaign Management**: Create, monitor, and manage multiple campaigns
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

## 🛠️ Installation

### 1. Install Redis (Windows)

Download and install Redis from:
- **Option A**: Download from https://redis.io/download
- **Option B**: Use Windows Subsystem for Linux (WSL)
- **Option C**: Use Docker: `docker run -d -p 6379:6379 redis:7-alpine`

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

You need to run 4 components:

### Terminal 1: Start Redis
```powershell
# If installed locally
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Terminal 2: Start Flask Backend
```powershell
cd backend
venv\Scripts\activate
python app.py
```

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
