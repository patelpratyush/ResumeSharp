# Testing the Billing System

## What I Fixed

### Issues Fixed:
1. **❌ Customer Portal 500 Error**: Was caused by missing Stripe customer
   **✅ Fixed**: Now creates customer automatically if missing

2. **❌ Database Permission Issues**: Was using ANON_KEY for admin operations  
   **✅ Fixed**: Now uses SERVICE_ROLE_KEY for database writes

3. **❌ User Email Retrieval**: Admin API calls were failing
   **✅ Fixed**: Added fallback strategies and better error handling

4. **❌ Missing Dependencies**: PyJWT wasn't installed
   **✅ Fixed**: Added to requirements.txt

## Quick Test Steps

### 1. Install Dependencies (if not done)
```bash
cd server
pip install PyJWT==2.8.0
```

### 2. Run Database Migrations (if not done)
```sql
-- Run this in Supabase SQL editor:
-- Copy paste from database_migrations.sql
```

### 3. Start the Application
```bash
# Terminal 1: Backend
cd server
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
npm run dev
```

### 4. Test the Flow

1. **Login/Signup** on your app
2. **Go to Settings** (`/settings`)
3. **Click "Manage Billing"** - This should work now!

## Expected Behavior

### ✅ What Should Work Now:

- **Manage Billing Button**: Creates Stripe customer portal
- **Upgrade Plan**: Redirects to pricing page
- **Pricing Page**: Shows plans and allows checkout
- **API Usage**: Tracks and displays correctly
- **Authentication**: Properly validates JWT tokens

### Debugging

If you still get errors, check the browser console and server logs. The server now prints detailed logs like:

```
Creating customer portal for user: abc123
No existing customer found, creating new one for user: abc123
Creating billing portal session for customer: cus_xyz
Portal session created successfully: https://billing.stripe.com/...
```

## What Happens When You Click "Manage Billing"

1. **Frontend** calls `/api/subscription/portal`
2. **Backend** gets user ID from JWT token
3. **Creates Stripe customer** if doesn't exist (using email from Supabase)
4. **Creates billing portal session** 
5. **Returns portal URL** to frontend
6. **Opens Stripe portal** in new tab

## Common Issues & Solutions

### "Failed to create customer portal" 
- Check server logs for specific error
- Verify Stripe keys are set correctly
- Make sure user is logged in

### "No authentication token available"
- User needs to be logged in via Supabase
- Check browser dev tools > Application > Local Storage

### Database errors
- Run the database migrations from `database_migrations.sql`
- Verify SUPABASE_SERVICE_ROLE_KEY is set correctly

## Test Results Expected

✅ **Customer Portal**: Should open Stripe billing portal  
✅ **Plan Display**: Shows current plan (Free/Pro/Ultimate)  
✅ **Usage Tracking**: Shows API calls used this month  
✅ **Authentication**: No more "user_123" placeholders  

The billing system should now be fully functional! 🎉