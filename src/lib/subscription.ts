/**
 * Subscription management utilities
 */

export type PlanTier = 'free' | 'pro' | 'ultimate';

export interface Plan {
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  api_calls_limit: number;
  features: string[];
  popular?: boolean;
}

export interface SubscriptionStatus {
  tier: PlanTier;
  status: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  stripe_customer_id?: string;
}

export interface UsageInfo {
  current_usage: number;
  limit: number;
  remaining: number;
  tier: PlanTier;
  percentage_used: number;
}

export const PLAN_FEATURES = {
  free: [
    'Resume analysis',
    'ATS optimization',
    'DOCX export',
    '5 API calls/month',
    'Basic support'
  ],
  pro: [
    'Everything in Free',
    'Bullet point rewriting',
    'Batch rewrite',
    'Advanced analytics',
    'Custom templates',
    '100 API calls/month',
    'Priority support'
  ],
  ultimate: [
    'Everything in Pro',
    'API access',
    'Team collaboration',
    'Unlimited storage',
    '1000 API calls/month',
    'Premium support'
  ]
};

export const PLAN_PRICES = {
  free: { monthly: 0, yearly: 0 },
  pro: { monthly: 19, yearly: 190 },
  ultimate: { monthly: 49, yearly: 490 }
};

export class SubscriptionAPI {
  private baseURL: string;

  constructor(baseURL: string = '/api/subscription') {
    this.baseURL = baseURL;
  }

  async getPlans(): Promise<{ plans: Record<string, Plan> }> {
    const response = await fetch(`${this.baseURL}/plans`);
    if (!response.ok) throw new Error('Failed to fetch plans');
    return response.json();
  }

  async getSubscriptionStatus(): Promise<{
    subscription: SubscriptionStatus;
    usage: UsageInfo;
  }> {
    const response = await fetch(`${this.baseURL}/status`, {
      headers: { 'Authorization': `Bearer ${this.getToken()}` }
    });
    if (!response.ok) throw new Error('Failed to fetch subscription status');
    return response.json();
  }

  async createCheckoutSession(
    planTier: PlanTier,
    billingCycle: 'monthly' | 'yearly' = 'monthly'
  ): Promise<{ checkout_url: string; session_id: string }> {
    const response = await fetch(`${this.baseURL}/checkout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify({
        plan_tier: planTier,
        billing_cycle: billingCycle,
        success_url: `${window.location.origin}/settings?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/settings`
      })
    });

    if (!response.ok) throw new Error('Failed to create checkout session');
    return response.json();
  }

  async createCustomerPortal(): Promise<{ portal_url: string }> {
    const response = await fetch(`${this.baseURL}/portal`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify({
        return_url: `${window.location.origin}/settings`
      })
    });

    if (!response.ok) throw new Error('Failed to create customer portal');
    return response.json();
  }

  async cancelSubscription(): Promise<{ cancelled: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });

    if (!response.ok) throw new Error('Failed to cancel subscription');
    return response.json();
  }

  async reactivateSubscription(): Promise<{ reactivated: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/reactivate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });

    if (!response.ok) throw new Error('Failed to reactivate subscription');
    return response.json();
  }

  async verifyCheckoutSession(sessionId: string): Promise<{
    verified: boolean;
    status: string;
    subscription_id?: string;
  }> {
    const response = await fetch(`${this.baseURL}/verify-session/${sessionId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });

    if (!response.ok) throw new Error('Failed to verify checkout session');
    return response.json();
  }

  private getToken(): string {
    // Get token from your auth system
    // This is a placeholder - implement according to your auth setup
    return localStorage.getItem('auth_token') || 'test';
  }
}

export const subscriptionAPI = new SubscriptionAPI();

export function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount);
}

export function getYearlySavings(monthlyPrice: number, yearlyPrice: number): number {
  return (monthlyPrice * 12) - yearlyPrice;
}

export function canUpgrade(currentTier: PlanTier, targetTier: PlanTier): boolean {
  const tiers = ['free', 'pro', 'ultimate'];
  return tiers.indexOf(targetTier) > tiers.indexOf(currentTier);
}