-- Database schema migrations for billing and subscription functionality
-- Run these commands in your Supabase SQL editor

-- 1. Add subscription fields to user_profiles table
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS subscription_id TEXT,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMP,
ADD COLUMN IF NOT EXISTS subscription_cancel_at_period_end BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS api_calls_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS api_calls_limit INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS api_calls_reset_date TIMESTAMP;

-- 2. Set default API limit reset date for existing users
UPDATE user_profiles 
SET api_calls_reset_date = (DATE_TRUNC('month', NOW()) + INTERVAL '1 month')::timestamp
WHERE api_calls_reset_date IS NULL;

-- 3. Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_stripe_customer_id ON user_profiles(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription_tier ON user_profiles(subscription_tier);

-- 4. Create a function to reset monthly usage (can be called by a cron job)
CREATE OR REPLACE FUNCTION reset_monthly_api_usage()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE user_profiles 
    SET 
        api_calls_used = 0,
        api_calls_reset_date = (DATE_TRUNC('month', NOW()) + INTERVAL '1 month')::timestamp,
        updated_at = NOW()
    WHERE api_calls_reset_date <= NOW();
END;
$$;

-- 5. Optional: Create a trigger to automatically set limits based on tier
CREATE OR REPLACE FUNCTION update_api_limits_on_tier_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Set API limits based on subscription tier
    IF NEW.subscription_tier = 'free' THEN
        NEW.api_calls_limit = 5;
    ELSIF NEW.subscription_tier = 'pro' THEN
        NEW.api_calls_limit = 100;
    ELSIF NEW.subscription_tier = 'ultimate' THEN
        NEW.api_calls_limit = 1000;
    END IF;
    
    RETURN NEW;
END;
$$;

-- Create the trigger
DROP TRIGGER IF EXISTS trigger_update_api_limits ON user_profiles;
CREATE TRIGGER trigger_update_api_limits
    BEFORE INSERT OR UPDATE OF subscription_tier
    ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_api_limits_on_tier_change();

-- 6. Update existing users with correct limits based on their tier
UPDATE user_profiles 
SET api_calls_limit = CASE 
    WHEN subscription_tier = 'free' THEN 5
    WHEN subscription_tier = 'pro' THEN 100
    WHEN subscription_tier = 'ultimate' THEN 1000
    ELSE 5
END;