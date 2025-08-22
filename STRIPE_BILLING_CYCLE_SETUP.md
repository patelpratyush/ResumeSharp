# Enable Monthly/Yearly Switching in Stripe Checkout

## 🐛 **Current Issue:**
When users go to Stripe checkout, they can't switch between monthly and yearly billing - they only see the option that was selected on your pricing page.

## ✅ **Solutions:**

### **Option 1: Stripe Product Configuration (Recommended)**

To enable billing cycle switching within Stripe checkout, you need to configure your products properly in Stripe Dashboard:

#### **Step 1: Configure Products in Stripe Dashboard**
1. **Go to Stripe Dashboard** → Products
2. **For each plan** (Pro, Ultimate), ensure both prices are attached to the **same product**:
   
   **Pro Plan Product:**
   - Product Name: "Pro Plan" 
   - Monthly Price: `price_1RygWs2LCeqGc1KEyimKNF7k` ($19/month)
   - Yearly Price: `price_1RygWs2LCeqGc1KERBDeZbVd` ($190/year)

   **Ultimate Plan Product:**
   - Product Name: "Ultimate Plan"
   - Monthly Price: `price_1RygXU2LCeqGc1KEjBFEwCNg` ($49/month) 
   - Yearly Price: `price_1RygXm2LCeqGc1KELIWzKh0Q` ($490/year)

#### **Step 2: Enable Recurring Price Options**
1. **Edit each product** in Stripe
2. **Set "Billing cycle anchor"** to "Current period"
3. **Enable "Allow customers to switch"** between pricing intervals
4. **Save changes**

### **Option 2: Use Stripe Pricing Tables (Alternative)**

Create a Stripe Pricing Table that includes both billing options:

1. **Go to Stripe Dashboard** → Pricing Tables
2. **Create new table** with both monthly and yearly options
3. **Embed the pricing table** in checkout instead of individual prices

### **Option 3: Frontend Enhancement (Current Solution)**

Our current implementation already allows users to choose billing cycle on the pricing page before going to Stripe. This is working correctly:

#### **How It Currently Works:**
1. **User visits** `/pricing` page
2. **Toggles monthly/yearly** switch
3. **Selects plan** → Redirects to Stripe with correct billing cycle
4. **Stripe shows** the selected billing option

## 🔧 **Technical Implementation:**

### **Current Code (Working):**
```typescript
// In Pricing.tsx - User selects billing cycle before Stripe
const { checkout_url } = await subscriptionAPI.createCheckoutSession(
  planTier,
  isYearly ? 'yearly' : 'monthly'  // ← This determines the billing cycle
);
```

### **Backend Configuration:**
```python
# In subscription.py - Selects correct price based on billing cycle
selected_price_id = monthly_price_id if billing_cycle == "monthly" else yearly_price_id

session = stripe.checkout.Session.create(
    line_items=[{
        'price': selected_price_id,  # ← Uses the correct price
        'quantity': 1,
    }],
    # ... other config
)
```

## 🎯 **User Experience Comparison:**

### **Current Flow (Working):**
```
Pricing Page → Select Plan → Toggle Monthly/Yearly → Go to Stripe → Pay
```

### **Enhanced Flow (Requires Stripe Config):**
```
Pricing Page → Select Plan → Go to Stripe → Switch Monthly/Yearly in Stripe → Pay
```

## 🚀 **Quick Fix for Better UX:**

Since changing Stripe product configuration might be complex, here's an immediate improvement:

### **Add Billing Cycle Selection Modal:**

Instead of just having a toggle on the pricing page, show a modal when users click "Upgrade":

```
Click "Upgrade to Pro" → Modal: "Choose Billing Cycle"
  ○ Monthly ($19/month)
  ○ Yearly ($190/year - Save $38!)
→ Continue to Stripe
```

## 🧪 **Current Status:**

### **✅ What's Working:**
- Monthly/yearly toggle on pricing page
- Correct prices sent to Stripe
- Users can choose billing cycle before checkout

### **❌ What's Missing:**
- Can't switch billing cycles within Stripe checkout
- Need to go back to pricing page to change cycle

## 💡 **Recommendation:**

**For now**: The current system works well. Users can choose their billing cycle on your pricing page.

**For future**: Configure Stripe products to enable in-checkout switching.

## 🔍 **Testing:**

1. **Go to** `/pricing`
2. **Toggle** between monthly/yearly
3. **Click upgrade** for any plan
4. **Verify** Stripe shows the correct price
5. **Complete test payment** with `4242 4242 4242 4242`

The billing cycle selection is working correctly - users just need to choose it on your pricing page before going to Stripe! 🎉