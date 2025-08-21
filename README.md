# ResumeSharp - AI Resume Optimization

A full-stack AI-powered application that helps job seekers sharpen their resumes for specific job descriptions with ATS-friendly insights, smart suggestions, and a complete subscription system.

## 🚀 Features

### Core Features
- **PDF Resume Parsing**: Extract text from PDF resumes with contact information detection
- **Resume Analysis**: Compare resumes against job descriptions with scoring
- **ATS Optimization**: Get insights on how ATS systems will read your resume
- **Smart Rewriting**: AI-powered bullet point improvements using OpenAI
- **Export Options**: Download optimized resumes in DOCX format
- **Real-time Preview**: See changes instantly with diff highlighting

### Business Features
- **Subscription System**: Three-tier pricing (Free, Pro, Ultimate)
- **Stripe Integration**: Secure payment processing with webhooks
- **Usage Tracking**: API call limits and usage enforcement
- **User Authentication**: Supabase-powered auth system
- **Dark Mode**: Complete dark/light theme support

## 🛠 Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for development and building
- **shadcn/ui** component library
- **Tailwind CSS** for styling
- **React Router** for navigation
- **React Query** for API state management

### Backend
- **FastAPI** (Python) with async support
- **Pydantic** for data validation
- **SQLAlchemy** for database operations
- **OpenAI API** for AI-powered rewriting
- **pdfplumber** for PDF text extraction
- **python-docx** for DOCX generation

### Infrastructure
- **Supabase** for database and authentication
- **Stripe** for payment processing
- **Rate limiting** with slowapi
- **CORS** and security middleware
- **Webhook** support for subscription events

## 📁 Project Structure

```
resumesharp/
├── src/                          # Frontend React application
│   ├── components/               # Reusable UI components
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── AnalyzeScreen.tsx    # Main analysis interface
│   │   ├── RewriteDrawer.tsx    # AI rewriting interface
│   │   └── ...
│   ├── pages/                   # Route components
│   │   ├── Index.tsx            # Landing page
│   │   ├── Dashboard.tsx        # Main dashboard
│   │   ├── Pricing.tsx          # Subscription plans
│   │   ├── Settings.tsx         # User settings & billing
│   │   └── ...
│   ├── lib/                     # Utilities and API clients
│   │   ├── api.ts              # Backend API client
│   │   ├── subscription.ts     # Stripe/subscription utilities
│   │   └── utils.ts            # Helper functions
│   └── integrations/
│       └── supabase/           # Supabase client setup
├── server/                      # Backend FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Configuration & subscription plans
│   │   ├── services/           # Business logic
│   │   │   ├── analyze.py      # Resume analysis engine
│   │   │   ├── rewrite.py      # AI rewriting service
│   │   │   ├── parse.py        # PDF parsing service
│   │   │   ├── subscription.py # Stripe integration
│   │   │   └── utils.py        # Contact extraction utilities
│   │   ├── routers/            # API route handlers
│   │   │   └── subscription.py # Subscription endpoints
│   │   ├── middleware/         # Custom middleware
│   │   │   └── usage_limiter.py # API usage enforcement
│   │   ├── schemas.py          # Pydantic models
│   │   ├── security.py         # Security utilities
│   │   └── error_handler.py    # Error handling
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   └── tests/                  # Backend tests
└── public/                     # Static assets
    ├── favicon.ico
    └── placeholder.svg
```

## 🔧 Development Setup

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.11+** and pip
- **Supabase account** (free tier available)
- **OpenAI API key**
- **Stripe account** (for payments)

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repository-url>
cd resumesharp

# Install frontend dependencies
npm install

# Install backend dependencies
cd server
pip install -r requirements.txt
pip install stripe supabase  # Additional dependencies for subscription system
```

### 2. Environment Configuration

Create `/server/.env` with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Stripe Configuration (Live Keys)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Development Settings
DEBUG_MODE=true
EXPOSE_CONFIG=true
ALLOWED_ORIGINS=*
FRONTEND_URL=http://localhost:8080

# Security Settings
VALIDATE_MIME_TYPES=true
RATE_LIMIT_ENABLED=true
MAX_UPLOAD_SIZE_MB=10
```

### 3. Database Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Run the following SQL to set up user profiles for ResumeSharp:

```sql
-- Create user_profiles table
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    subscription_tier TEXT DEFAULT 'free',
    subscription_status TEXT DEFAULT 'active',
    subscription_id TEXT,
    stripe_customer_id TEXT,
    subscription_current_period_end TIMESTAMP,
    subscription_cancel_at_period_end BOOLEAN DEFAULT false,
    api_calls_used INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 5,
    api_calls_reset_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);
```

### 4. Stripe Setup

1. Create products and prices in Stripe Dashboard:
   - **Pro Plan**: $19/month, $190/year
   - **Ultimate Plan**: $49/month, $490/year

2. Create webhook endpoint pointing to: `https://your-domain.com/api/subscription/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`

3. Update price IDs in `/server/app/config.py`:
   ```python
   SUBSCRIPTION_PLANS = {
       PlanTier.PRO: {
           "stripe_price_id_monthly": "price_your_pro_monthly_id",
           "stripe_price_id_yearly": "price_your_pro_yearly_id",
           # ...
       }
       # ...
   }
   ```

### 5. Start Development Servers

```bash
# Terminal 1: Start backend server
cd server
PYTHONPATH=/Users/your-username/path/to/resumesharp/server python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend server
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 💳 Subscription System

### Plan Tiers
- **Free**: 5 API calls/month
- **Pro**: $19/month or $190/year (100 API calls/month)
- **Ultimate**: $49/month or $490/year (1000 API calls/month)

### Features by Tier
- **Free**: Resume analysis, ATS optimization, DOCX export
- **Pro**: Everything in Free + bullet rewriting, batch rewrite, advanced analytics, custom templates
- **Ultimate**: Everything in Pro + priority support, API access, team collaboration, unlimited storage

### API Endpoints
- `GET /api/subscription/plans` - Get available plans
- `GET /api/subscription/status` - Get user subscription status
- `POST /api/subscription/checkout` - Create Stripe checkout session
- `POST /api/subscription/portal` - Access customer portal
- `POST /api/subscription/webhook` - Handle Stripe webhooks

## 🧪 Testing

```bash
# Run end-to-end tests
npm run test:e2e

# Run tests with UI
npm run test:e2e:ui

# Run backend tests
cd server
pytest
```

## 🚀 Deployment

### **Step 1: Deploy Backend First**

**Railway (Recommended):**
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Select the `/server` directory as the root
4. Add environment variables:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   OPENAI_API_KEY=your_openai_api_key
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   DEBUG_MODE=false
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
   FRONTEND_URL=https://your-frontend-domain.vercel.app
   ```
5. Deploy and copy the backend URL (e.g., `https://your-app.railway.app`)

### **Step 2: Deploy Frontend**

**Vercel (Recommended):**
1. Go to [vercel.com](https://vercel.com)
2. Connect your GitHub repository
3. **Set Environment Variables:**
   ```env
   VITE_API_URL=https://your-backend-domain.railway.app
   ```
4. **Build Settings:**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

**Netlify:**
1. Go to [netlify.com](https://netlify.com)
2. Connect your GitHub repository
3. **Build Settings:**
   - Build Command: `npm run build`
   - Publish Directory: `dist`
4. **Environment Variables:**
   ```env
   VITE_API_URL=https://your-backend-domain.railway.app
   ```

### **Step 3: Update Webhook URL**
- Go to Stripe Dashboard → Webhooks
- Update endpoint URL to: `https://your-backend-domain.railway.app/api/subscription/webhook`

### **Alternative: Full-Stack on Vercel**
Create `vercel.json`:
```json
{
  "builds": [
    {
      "src": "server/app/main.py",
      "use": "@vercel/python"
    },
    {
      "src": "package.json",
      "use": "@vercel/static-build"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "server/app/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "VITE_API_URL": "/api"
  }
}
```

## 📄 API Documentation

When the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 🔒 Security Features

- File upload validation with MIME type checking
- Rate limiting on API endpoints
- CORS configuration
- Input sanitization
- Webhook signature verification
- Secure environment variable handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📝 License

This project is private. All rights reserved.