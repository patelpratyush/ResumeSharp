# Supabase Setup Guide for Tailor Flow

## 🚀 Quick Start (5 minutes)

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up
2. Click "New Project"
3. Choose organization, name your project (e.g., "tailor-flow")
4. Set a strong database password
5. Choose region closest to your users
6. Click "Create new project"

### Step 2: Get Your Credentials
1. Go to **Settings** → **API**
2. Copy these values:
   ```
   Project URL: https://xxxxx.supabase.co
   anon public: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   service_role: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### Step 3: Set Up Database Schema
1. Go to **SQL Editor** in Supabase dashboard
2. Copy the entire contents of `database/schema.sql` 
3. Paste into SQL Editor and click **"Run"**
4. ✅ You should see "Success. No rows returned" for each statement

### Step 4: Configure Environment Variables
Create `.env` in your server directory:

```bash
# Copy from .env.example and fill in your values:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Keep existing settings:
DEBUG_MODE=false
ALLOWED_ORIGINS=http://localhost:3000  # Your frontend URL
```

### Step 5: Test the Setup
```bash
cd server
pip install supabase

# Test connection:
python -c "
from app.database import supabase, db_manager
print('✅ Supabase connected!' if supabase else '❌ Connection failed')
print('✅ Database manager ready!' if db_manager else '❌ DB manager failed')
"
```

## 🔧 Development vs Production

### Development (Local)
```bash
# .env for local development
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
DEBUG_MODE=true
ALLOWED_ORIGINS=http://localhost:3000
```

### Production (Render/Vercel)
```bash
# Environment variables in Render dashboard:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
DEBUG_MODE=false
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

## 📊 Database Schema Overview

Your database now has these tables:

### Core Tables
- **`user_profiles`** - Extended user info (subscription, API limits)
- **`resumes`** - User's saved resumes with full content
- **`job_descriptions`** - Saved JDs for analysis
- **`analyses`** - Complete analysis history with scores
- **`user_settings`** - User preferences (max words, export style, etc.)
- **`rewrite_history`** - AI rewrite suggestions and acceptances

### Security Features
- **Row Level Security (RLS)** - Users can only see their own data
- **Automatic user creation** - Profile created on signup
- **API rate limiting** - Per-user usage tracking

## 🔑 Authentication Flow

### How Auth Works
1. **Frontend**: User signs up/logs in with Supabase Auth UI
2. **Frontend**: Gets JWT token from Supabase
3. **Frontend**: Sends token in `Authorization: Bearer <token>` header
4. **Backend**: Validates token with Supabase and extracts user ID
5. **Backend**: All database operations are user-scoped automatically

### Backend Integration
```python
# Your endpoints now work like this:
from app.auth import auth_required

@app.post("/api/user/resumes")
async def save_resume(user: AuthUser = Depends(auth_required)):
    # user.id is automatically extracted from JWT
    resume_id = await db_manager.save_resume(user.id, ...)
    return {"resume_id": resume_id}
```

## 🎯 Frontend Integration (Next Steps)

You'll need to add Supabase client to your frontend:

```bash
# In your frontend directory:
npm install @supabase/supabase-js @supabase/auth-ui-react @supabase/auth-ui-shared
```

Key frontend changes needed:
1. **Auth Context** - Wrap app with Supabase auth provider
2. **Login/Signup UI** - Add auth components  
3. **Protected Routes** - Redirect unauthenticated users
4. **API Updates** - Include JWT token in requests
5. **User Data** - Replace localStorage with API calls

## 🔧 API Usage Limits

The system automatically tracks API usage per user:

### Free Tier (Default)
- **100 API calls** per user
- Includes: analysis, rewrite, parse, export
- Counter resets monthly (you can modify this)

### Upgrade System Ready
- Database supports `subscription_tier` field
- Easy to add "pro" and "enterprise" tiers
- Can increase limits per tier

## ✅ Verification Checklist

After setup, verify these work:

### Database Connection
```bash
python -c "from app.database import supabase; print('✅' if supabase else '❌')"
```

### Schema Created
- Go to Supabase **Table Editor**
- Should see: `user_profiles`, `resumes`, `analyses`, etc.

### RLS Enabled
- Click any table → **Settings**
- Should show "Row Level Security: Enabled"

### Test User Creation
- Go to **Authentication** → **Users**
- Click "Add user" to create a test user
- Check that `user_profiles` table gets a new row automatically

## 🚀 Ready for Frontend!

With Supabase configured, your backend now supports:
- ✅ **User authentication** with JWT validation
- ✅ **Per-user data storage** with automatic security
- ✅ **API rate limiting** per user  
- ✅ **Analysis history** persistence
- ✅ **Resume management** with full CRUD
- ✅ **Settings sync** across devices

Next: Add Supabase auth to your frontend and replace localStorage with API calls!