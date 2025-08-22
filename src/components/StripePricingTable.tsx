import { useEffect, useRef } from 'react';
import { STRIPE_CONFIG } from '@/config/stripe';

interface StripePricingTableProps {
  pricingTableId?: string;
  publishableKey?: string;
  customerEmail?: string;
  successUrl?: string;
  cancelUrl?: string;
  clientReferenceId?: string;
}

export default function StripePricingTable({ 
  pricingTableId = STRIPE_CONFIG.PRICING_TABLE_ID, 
  publishableKey = STRIPE_CONFIG.PUBLISHABLE_KEY,
  customerEmail,
  successUrl,
  cancelUrl,
  clientReferenceId
}: StripePricingTableProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scriptLoadedRef = useRef(false);

  useEffect(() => {
    // Load Stripe pricing table script if not already loaded
    if (!scriptLoadedRef.current) {
      const script = document.createElement('script');
      script.src = 'https://js.stripe.com/v3/pricing-table.js';
      script.async = true;
      document.head.appendChild(script);
      scriptLoadedRef.current = true;
    }

    // Create the pricing table element
    if (containerRef.current) {
      const pricingTable = document.createElement('stripe-pricing-table');
      pricingTable.setAttribute('pricing-table-id', pricingTableId);
      pricingTable.setAttribute('publishable-key', publishableKey);
      
      // Set optional attributes if provided
      if (customerEmail) {
        pricingTable.setAttribute('customer-email', customerEmail);
      }
      
      if (successUrl) {
        pricingTable.setAttribute('customer-session-redirect-on-success', successUrl);
      }
      
      if (cancelUrl) {
        pricingTable.setAttribute('customer-session-redirect-on-cancel', cancelUrl);
      }
      
      if (clientReferenceId) {
        pricingTable.setAttribute('client-reference-id', clientReferenceId);
      }
      
      // Clear container and add pricing table
      containerRef.current.innerHTML = '';
      containerRef.current.appendChild(pricingTable);
    }

    // Cleanup
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [pricingTableId, publishableKey, customerEmail, successUrl, cancelUrl, clientReferenceId]);

  return <div ref={containerRef} className="stripe-pricing-table-container" />;
}