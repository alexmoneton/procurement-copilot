# 🚀 Deploy TenderPulse Frontend to Vercel

## ✅ Backend API is LIVE: https://api.tenderpulse.eu

Now let's get your frontend live in 5 minutes!

## 📋 Step-by-Step Frontend Deployment:

### **Step 1: Go to Vercel Dashboard**
1. Open **https://vercel.com**
2. Click **"Sign up"** or **"Login"**
3. Choose **"Continue with GitHub"**
4. Authorize Vercel to access your GitHub

### **Step 2: Import Your Project**
1. In Vercel dashboard, click **"New Project"**
2. Find your **`procurement-copilot`** repository
3. Click **"Import"**
4. **Important**: Set **Root Directory** to `frontend`
5. Click **"Deploy"**

### **Step 3: Configure Environment Variables**
While deployment is running, add these environment variables:

1. In Vercel dashboard → Your Project → **"Settings"** → **"Environment Variables"**
2. Add these variables for **Production**:

```
NEXT_PUBLIC_BACKEND_URL=https://api.tenderpulse.eu
NEXT_PUBLIC_APP_URL=https://tenderpulse.eu
NEXT_PUBLIC_ENVIRONMENT=production

# Clerk (use test keys for now)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here

# Stripe (use test keys for now)  
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
NEXT_PUBLIC_STRIPE_PRICE_IDS={"starter":"price_starter","pro":"price_pro","team":"price_team"}
```

### **Step 4: Get Your Vercel URL**
1. After deployment completes, you'll get a URL like:
   `https://procurement-copilot-abc123.vercel.app`
2. **Write this down** - you'll need it for DNS!

### **Step 5: Add Custom Domain**
1. In Vercel dashboard → **"Settings"** → **"Domains"**
2. Click **"Add"**
3. Enter: `tenderpulse.eu`
4. Vercel will show you DNS instructions

### **Step 6: Configure DNS in Namecheap**
1. Go back to Namecheap → Advanced DNS
2. Add another CNAME record:
   - **Type**: `CNAME`
   - **Host**: `@` (or leave empty for root domain)
   - **Value**: `cname.vercel-dns.com`
3. Click **"Save All Changes"**

### **Step 7: Test Your Live Website**
```bash
# Test frontend (after DNS propagates - 5-30 minutes)
curl https://tenderpulse.eu

# Should return HTML with "TenderPulse" title
```

## 🎯 **Expected Result:**

✅ **Frontend**: https://tenderpulse.eu  
✅ **API**: https://api.tenderpulse.eu  
✅ **TenderPulse branding**: EU colors, logo, fonts  
✅ **Working data**: Connected to live API with 139 tenders  
✅ **Self-service signup**: Users can create accounts  
✅ **Ready for customers**: No demos needed!

## 🔧 **If You Get Stuck:**

### **Build Errors:**
- Make sure Root Directory is set to `frontend`
- Check build logs in Vercel dashboard

### **Environment Variables:**
- Add them BEFORE the first deployment
- Or redeploy after adding them

### **DNS Issues:**
- DNS can take up to 48 hours to propagate
- Test with direct Vercel URL first

## 🎉 **Success Criteria:**

When done, you should have:
- ✅ https://tenderpulse.eu loads with TenderPulse branding
- ✅ https://api.tenderpulse.eu/api/v1/health returns {"status":"ok"}
- ✅ Users can browse 139+ live European tenders
- ✅ Self-service signup and filter creation works
- ✅ Ready to start customer acquisition immediately!

---

**Start with Step 1 above - your frontend will be live in 15-30 minutes!** 🚀
