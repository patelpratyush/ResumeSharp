import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Crown, Users } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import StripePricingTable from '@/components/StripePricingTable';

const planIcons = {
  pro: Crown,
  ultimate: Users,
};

const planDescriptions = {
  pro: 'Perfect for serious job seekers',
  ultimate: 'For power users and professionals',
};

export default function Checkout() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  
  const selectedPlan = searchParams.get('plan') as 'pro' | 'ultimate' | null;
  const userEmail = searchParams.get('email') || user?.email;
  const userId = searchParams.get('user_id') || user?.id;

  useEffect(() => {
    // Redirect if no plan selected or user not authenticated
    if (!selectedPlan || (!user && !userId)) {
      navigate('/auth');
      return;
    }
  }, [selectedPlan, user, userId, navigate]);

  if (!selectedPlan) {
    return null;
  }

  const Icon = planIcons[selectedPlan];
  const baseUrl = window.location.origin;
  const successUrl = `${baseUrl}/dashboard?welcome=true&plan=${selectedPlan}`;
  const cancelUrl = `${baseUrl}/pricing?checkout_cancelled=true`;

  return (
    <div className="container py-8 animate-fade-in">
      <Helmet>
        <title>Checkout - {selectedPlan} Plan – ResumeSharp</title>
        <meta name="description" content={`Complete your ${selectedPlan} plan subscription with monthly or yearly billing options.`} />
      </Helmet>

      {/* Header */}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/pricing')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Pricing
          </Button>
        </div>

        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Icon className={`w-12 h-12 ${
              selectedPlan === 'pro' ? 'text-blue-600' : 'text-purple-600'
            }`} />
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-4 capitalize">
            {selectedPlan} Plan Checkout
          </h1>
          <p className="text-xl text-muted-foreground">
            {planDescriptions[selectedPlan]}
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Choose your billing cycle below - you can change it anytime
          </p>
        </div>

        {/* Stripe Pricing Table */}
        <div className="max-w-2xl mx-auto">
          <Card className="rounded-2xl shadow-soft border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="text-center">Choose Your Billing Cycle</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gradient-to-br from-background via-background to-muted/20 rounded-lg p-8">
                <StripePricingTable 
                  customerEmail={userEmail}
                  successUrl={successUrl}
                  cancelUrl={cancelUrl}
                  clientReferenceId={userId}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Benefits reminder */}
        <div className="max-w-2xl mx-auto mt-8 text-center">
          <div className="bg-muted/30 rounded-lg p-6">
            <h3 className="font-semibold mb-2">💡 Why choose yearly billing?</h3>
            <p className="text-sm text-muted-foreground">
              Save up to 20% with yearly billing and get 2 months free! 
              You can always switch back to monthly billing later.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}