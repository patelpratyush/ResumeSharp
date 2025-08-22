// Stripe configuration constants
export const STRIPE_CONFIG = {
  PRICING_TABLE_ID: 'prctbl_1Rz0fE2LCeqGc1KEuuqfv6DD',
  PUBLISHABLE_KEY: 'pk_live_51Po96R2LCeqGc1KEUlI39oyOZMqzpizdFvXQ18FmnXzzjSF655OhqL7YIe0kiKQfzu0gkvJt5nUmvKbjwDOQVTkk006FpUvJHw',
} as const;

export function createPricingPageUrl(params: {
  email?: string;
  clientReferenceId?: string;
  successUrl?: string;
  cancelUrl?: string;
  useStripeTable?: boolean;
  selectedPlan?: string;
}) {
  const { email, clientReferenceId, successUrl, cancelUrl, useStripeTable = true, selectedPlan } = params;
  
  // Since Stripe pricing tables are embedded components, we redirect to our pricing page
  // with parameters that will auto-show the Stripe table and pre-fill user info
  let url = '/pricing';
  
  const queryParams = new URLSearchParams();
  
  if (useStripeTable) {
    queryParams.append('stripe_table', 'true');
  }
  
  if (email) {
    queryParams.append('email', email);
  }
  
  if (clientReferenceId) {
    queryParams.append('user_id', clientReferenceId);
  }
  
  if (selectedPlan) {
    queryParams.append('plan', selectedPlan);
  }
  
  if (successUrl) {
    queryParams.append('success_url', successUrl);
  }
  
  if (cancelUrl) {
    queryParams.append('cancel_url', cancelUrl);
  }
  
  const queryString = queryParams.toString();
  if (queryString) {
    url += `?${queryString}`;
  }
  
  return url;
}