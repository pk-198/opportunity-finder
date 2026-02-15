# to run
## venv here and uses 3002 and 8002 ports
cd backend
source venv/bin/activate
python main.py

cd frontend
npm run dev

# Gmail Email Analysis Automation

An internal tool that analyzes Gmail emails from specific senders (F5bot Reddit alerts, HARO requests) using LLM prompts and displays actionable insights in real-time on a web interface.

## 🎯 Purpose

Identify engagement opportunities where Dograh AI can be promoted or provide value by analyzing:
- Reddit posts from F5bot alerts
- HARO (Help A Reporter Out) media opportunities
- Other email sources (configurable)

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14 (TypeScript, React, Tailwind CSS)
- **LLM**: OpenAI GPT-4o-mini or GROQ (switchable)
- **Email**: Gmail API with OAuth
- **Storage**: In-memory only (24hr auto-cleanup)

### Project Structure
```
├── backend/
│   ├── main.py              # FastAPI app
│   ├── workflow.py          # Central orchestrator
│   ├── email_service.py     # Gmail API integration
│   ├── llm_service.py       # LLM provider abstraction
│   ├── task_manager.py      # In-memory task storage
│   ├── prompts.py           # Prompt loader
│   ├── config/
│   │   ├── prompts.yaml     # LLM prompts
│   │   └── senders.json     # Sender configurations
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main form page
│   │   ├── analysis/
│   │   │   └── page.tsx     # Results page
│   │   └── components/      # React components
│   └── lib/
│       └── api.ts           # API client
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn
- Gmail account
- OpenAI API key OR GROQ API key
- Google Cloud Project with Gmail API enabled

### Step 1: Google Cloud Setup (Gmail API)

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" > "New Project"
   - Enter project name (e.g., "Email Analysis Tool")
   - Click "Create"

2. **Enable Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

3. **Configure OAuth Consent Screen** (Required for OAuth):
   - Go to "APIs & Services" > "OAuth consent screen"
   - **User Type**: Select "External" (for personal Gmail accounts)
   - Click "Create"

   **App Information**:
   - App name: "Email Analysis Tool"
   - User support email: Your email address
   - Developer contact email: Your email address

   **Scopes** (Click "Add or Remove Scopes"):
   - Search for "Gmail API"
   - Select: `https://www.googleapis.com/auth/gmail.readonly`
   - Click "Update" then "Save and Continue"

   **Test Users** (Optional):
   - Add your Gmail address if you want to test before publishing
   - Click "Save and Continue"

   **Summary**:
   - Review and click "Back to Dashboard"
   - **Publishing Status**: Keep as "Testing" (no verification needed for personal use)

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" > "OAuth client ID"
   - **Application type**: Select "Desktop app"
     - ℹ️ **Why Desktop?** This tool runs locally and uses `localhost` for OAuth callback
     - No JavaScript origins or redirect URIs needed (handled automatically)
   - Name: "Email Analysis Desktop Client"
   - Click "Create"
   - Click "OK" on the confirmation dialog

5. **Download Credentials**:
   - Find your OAuth 2.0 Client ID in the credentials list
   - Click the download icon (⬇️) on the right
   - Save the JSON file
   - Rename it to `credentials.json`
   - **Move to**: Place in the `backend/` directory

**Important Notes**:
- ✅ Keep Publishing Status as "Testing" for personal/internal use (supports up to 100 test users)
- ✅ First run will open a browser for Gmail OAuth consent - this is normal
- ✅ `token.json` will be created automatically after first successful authentication
- ⚠️ Never commit `credentials.json` or `token.json` to version control (already in `.gitignore`)

### Step 2: Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` file** with your credentials:
   ```env
   # Gmail API (credentials.json should be in backend/)
   GMAIL_CREDENTIALS_FILE=credentials.json
   GMAIL_TOKEN_FILE=token.json

   # LLM Provider (choose one)
   LLM_PROVIDER=openai  # or "groq"

   # OpenAI Configuration
   OPENAI_API_KEY=your_actual_openai_api_key_here
   OPENAI_MODEL=gpt-4o-mini

   # GROQ Configuration (alternative)
   # GROQ_API_KEY=your_actual_groq_api_key_here
   # GROQ_MODEL=llama-3.1-70b-versatile

   # LLM Timeout
   LLM_TIMEOUT=180

   # Batch Processing
   DEFAULT_BATCH_SIZE=5
   DEFAULT_EMAIL_LIMIT=50

   # Task Cleanup
   TASK_CLEANUP_HOURS=24

   # Logging
   LOG_LEVEL=INFO
   ```

### Step 3: Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

## 🧪 Testing Instructions

### Start Backend Server

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Start FastAPI server**:
   ```bash
   python main.py
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8002
   ```

4. **First-time Gmail OAuth**:
   - On first run, a browser window will open
   - Log in with your Gmail account
   - Grant permissions to read emails
   - `token.json` will be created automatically

### Start Frontend Server

1. **Open new terminal window**

2. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

3. **Start Next.js development server**:
   ```bash
   npm run dev
   ```

   You should see:
   ```
   ▲ Next.js 14.1.0
   - Local:        http://localhost:3002
   ```

### Test the Application

1. **Open browser**: Navigate to http://localhost:3002

2. **Select a sender** from the dropdown:
   - F5bot Reddit Alerts
   - HARO - Help A Reporter Out
   - HARO - Peter Shankman

3. **Configure analysis**:
   - Number of Emails: 50 (default)
   - Batch Size: 5 (default)

4. **Click "Analyze Emails"**:
   - You'll be redirected to results page
   - Progress bar shows batch processing
   - Results appear incrementally (polling every 15 seconds)

5. **View results**:
   - Each batch shows LLM analysis
   - Hyperlinks are preserved
   - Errors are displayed per batch

## 🔍 API Endpoints

### Backend API (http://localhost:8002)

1. **POST /api/analyze** - Start analysis
   ```json
   {
     "sender_id": "f5bot",
     "email_limit": 50,
     "batch_size": 5
   }
   ```

2. **GET /api/status/{task_id}** - Poll for results
   ```json
   {
     "task_id": "abc123",
     "status": "processing",
     "progress": "3/10",
     "results": [...]
   }
   ```

3. **GET /api/senders** - Get configured senders
   ```json
   {
     "senders": [...]
   }
   ```

4. **GET /health** - Health check
   ```json
   {
     "status": "healthy"
   }
   ```

## 📝 Configuration

### Adding New Senders

Edit `backend/config/senders.json`:
```json
{
  "id": "new_sender",
  "name": "Sender Name",
  "email": "sender@example.com",
  "description": "Description",
  "expected_volume": "10-50 emails daily",
  "prompt_key": "sender_prompt"
}
```

### Adding New Prompts

Edit `backend/config/prompts.yaml`:
```yaml
sender_prompt:
  system_prompt: |
    You are an expert at analyzing...
  user_prompt: |
    Analyze the following emails:
    {email_content}
```

## 🐛 Troubleshooting

### Backend Issues

1. **Gmail API Error**:
   - Ensure `credentials.json` is in backend directory
   - Delete `token.json` and re-authenticate
   - Check Gmail API is enabled in Google Cloud Console

2. **LLM Timeout**:
   - Default timeout is 180 seconds
   - Adjust `LLM_TIMEOUT` in `.env` if needed

3. **Import Errors**:
   - Ensure virtual environment is activated
   - Re-run `pip install -r requirements.txt`

### Frontend Issues

1. **API Connection Error**:
   - Ensure backend is running on port 8002
   - Check CORS is enabled (already configured)

2. **TypeScript Errors**:
   - Run `npm install` again
   - Check `tsconfig.json` is present

3. **Polling Not Working**:
   - Check browser console for errors
   - Verify task_id is in URL query params

## 🔒 Security Notes

- **Never commit** `.env` or `credentials.json` to version control
- Token and credentials files are in `.gitignore`
- In-memory storage only - no persistent data
- OAuth tokens expire and auto-refresh

## 📊 Performance

- **Batch processing**: Default 5 emails per batch
- **LLM timeout**: 180 seconds per call
- **Polling interval**: 15 seconds
- **Auto-cleanup**: Tasks deleted after 24 hours

## 🎨 Customization

### Changing LLM Provider

Edit `backend/.env`:
```env
LLM_PROVIDER=groq  # Switch to GROQ
GROQ_API_KEY=your_groq_key
```

### Adjusting Batch Size

Default: 5 emails per batch
- Small batches: Faster feedback, more LLM calls
- Large batches: Fewer calls, slower feedback

### Modifying Polling Interval

Edit `frontend/app/analysis/page.tsx`:
```typescript
const intervalId = setInterval(() => {
  if (polling) {
    fetchStatus();
  }
}, 15000);  // Change 15000 (15 seconds) to desired interval
```

## 📚 Next Steps

1. **Run the backend**: `python backend/main.py`
2. **Run the frontend**: `npm run dev` (in frontend directory)
3. **Open browser**: http://localhost:3002
4. **Select sender and analyze emails**
5. **View results incrementally**

## 💡 Tips

- Use smaller email limits (10-20) for initial testing
- Check backend logs for detailed execution flow
- Results are lost after 24 hours (in-memory only)
- Gmail API has rate limits - be mindful of frequent polling

## 🆘 Support

For issues or questions:
1. Check backend logs for errors
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Ensure Gmail OAuth is working

---

**Built with minimal, elegant code following the must_follow_rules.md guidelines.**
