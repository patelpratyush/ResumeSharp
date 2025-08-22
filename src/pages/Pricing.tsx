import { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Check, Crown, Zap, Users } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { subscriptionAPI, formatPrice, getYearlySavings, PLAN_FEATURES, PLAN_PRICES, type PlanTier } from '@/lib/subscription';

const planIcons = {
  free: Zap,
  pro: Crown,
  ultimate: Users,
};

const planColors = {
  free: 'border-gray-200 dark:border-gray-700',
  pro: 'border-blue-200 dark:border-blue-700 ring-2 ring-blue-100 dark:ring-blue-900',
  ultimate: 'border-purple-200 dark:border-purple-700',
};

export default function Pricing() {
  const [isYearly, setIsYearly] = useState(false);
  const [loading, setLoading] = useState<PlanTier | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();
  const navigate = useNavigate();

  // Check for URL parameters and auto-configure page
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    
    // Check for signup cancellation
    if (params.get('signup_cancelled') === 'true') {
      toast({
        title: "Checkout Cancelled",
        description: "You can still upgrade to a paid plan anytime from this page.",
        variant: "default",
      });
    }
    
    // Clean up URL after processing
    if (params.toString()) {
      window.history.replaceState({}, '', '/pricing');
    }
  }, [toast]);

  const handleSelectPlan = async (planTier: PlanTier) => {
    if (!user) {
      navigate('/auth');
      return;
    }

    if (planTier === 'free') {
      navigate('/settings');
      return;
    }

    setLoading(planTier);

    try {
      const { checkout_url } = await subscriptionAPI.createCheckoutSession(
        planTier,
        isYearly ? 'yearly' : 'monthly'
      );

      // Redirect to Stripe checkout
      window.location.href = checkout_url;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      toast({
        title: 'Error',
        description: 'Failed to start checkout process. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(null);
    }
  };

  const getPlanPrice = (tier: PlanTier) => {
    const prices = PLAN_PRICES[tier];
    return isYearly ? prices.yearly : prices.monthly;
  };

  const getMonthlyPrice = (tier: PlanTier) => {
    const prices = PLAN_PRICES[tier];
    return isYearly ? prices.yearly / 12 : prices.monthly;
  };

  return (
    <div className="container py-8 animate-fade-in">
      <Helmet>
        <title>Pricing – ResumeSharp</title>
        <meta name="description" content="Choose the perfect plan for your resume optimization needs. Start free or upgrade for advanced features." />
        <link rel="canonical" href="/pricing" />
      </Helmet>

      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          Start free and upgrade as you grow. All plans include core resume optimization features.
        </p>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <Label htmlFor="billing-toggle" className={!isYearly ? 'font-semibold' : ''}>
            Monthly
          </Label>
          <Switch
            id="billing-toggle"
            checked={isYearly}
            onCheckedChange={setIsYearly}
          />
          <Label htmlFor="billing-toggle" className={isYearly ? 'font-semibold' : ''}>
            Yearly
          </Label>
          {isYearly && (
            <Badge variant="secondary" className="ml-2">
              Save up to ${getYearlySavings(PLAN_PRICES.ultimate.monthly, PLAN_PRICES.ultimate.yearly)}
            </Badge>
          )}
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {Object.entries(PLAN_PRICES).map(([tier, prices]) => {
          const tierKey = tier as PlanTier;
          const Icon = planIcons[tierKey];
          const isPopular = tierKey === 'pro';
          const price = getPlanPrice(tierKey);
          const monthlyPrice = getMonthlyPrice(tierKey);

          return (
            <Card
              key={tier}
              className={`relative rounded-2xl shadow-soft ${planColors[tierKey]} ${
                isPopular ? 'scale-105' : ''
              }`}
            >
              {isPopular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
                    Most Popular
                  </Badge>
                </div>
              )}

              <CardHeader className="text-center pb-4">
                <div className="flex items-center justify-center mb-4">
                  <Icon className={`w-8 h-8 ${
                    tierKey === 'free' ? 'text-gray-600' :
                    tierKey === 'pro' ? 'text-blue-600' : 'text-purple-600'
                  }`} />
                </div>
                <CardTitle className="text-2xl font-bold capitalize">
                  {tier}
                </CardTitle>
                <div className="text-center">
                  <div className="text-4xl font-bold">
                    {price === 0 ? 'Free' : formatPrice(monthlyPrice)}
                  </div>
                  {price > 0 && (
                    <div className="text-sm text-muted-foreground">
                      {isYearly ? (
                        <>
                          billed yearly ({formatPrice(price)})
                        </>
                      ) : (
                        'per month'
                      )}
                    </div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features */}
                <ul className="space-y-3">
                  {PLAN_FEATURES[tierKey].map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA Button */}
                <div className="pt-6">
                  <Button
                    onClick={() => handleSelectPlan(tierKey)}
                    disabled={loading === tierKey}
                    className={`w-full ${
                      tierKey === 'free' 
                        ? 'variant-outline' 
                        : isPopular
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700'
                        : ''
                    }`}
                    variant={tierKey === 'free' ? 'outline' : 'default'}
                  >
                    {loading === tierKey ? (
                      'Loading...'
                    ) : tierKey === 'free' ? (
                      'Get Started'
                    ) : (
                      `Upgrade to ${tier}`
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>


      {/* FAQ or Additional Info */}
      <div className="max-w-4xl mx-auto mt-16">
        <Card className="rounded-2xl shadow-soft">
          <CardHeader>
            <CardTitle className="text-center">Frequently Asked Questions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Can I change plans anytime?</h3>
              <p className="text-muted-foreground">
                Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately for upgrades,
                or at the end of your billing period for downgrades.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">What happens if I exceed my API limit?</h3>
              <p className="text-muted-foreground">
                You'll receive notifications as you approach your limit. Once exceeded, you'll need to upgrade
                your plan or wait until next month for your limit to reset.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Is there a free trial for paid plans?</h3>
              <p className="text-muted-foreground">
                Start with our free plan to try the core features. You can upgrade anytime to access
                advanced features and higher limits.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">How does billing work?</h3>
              <p className="text-muted-foreground">
                We use Stripe for secure billing. You'll be charged automatically based on your selected
                billing cycle. You can update payment methods and view invoices in your account settings.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}