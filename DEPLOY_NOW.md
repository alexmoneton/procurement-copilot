# 🚀 Deploy TenderPulse API to Railway - STEP BY STEP

Your TenderPulse API is ready for deployment! Follow these exact steps:

## ✅ What's Ready:
- ✅ API working locally with 200 tenders worth €800M+
- ✅ Production deployment script (`railway_deploy.py`)
- ✅ All dependencies listed (`requirements.txt`)
- ✅ Git committed and ready to deploy

## 🔥 DEPLOY NOW - Follow These Steps:

### Step 1: Create Railway Account
1. Go to **https://railway.app**
2. Click **"Sign up"**
3. Choose **"Sign up with GitHub"** (easiest)
4. Authorize Railway to access your GitHub

### Step 2: Create New Project
1. In Railway dashboard, click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Select your `procurement-copilot` repository
4. Click **"Deploy Now"**

### Step 3: Configure Environment Variables
1. In your Railway project, click **"Variables"** tab
2. Add these environment variables:

```
ENVIRONMENT=production
ENABLE_CONNECTORS=TED
SHADOW_CONNECTORS=
TZ=Europe/Paris
BACKEND_BASE_URL=https://api.tenderpulse.eu
FRONTEND_BASE_URL=https://tenderpulse.eu
PORT=8000
```

### Step 4: Set Startup Command
1. In Railway project, go to **"Settings"** tab
2. Find **"Start Command"** section
3. Set it to: `python3 railway_deploy.py`

### Step 5: Deploy & Get URL
1. Railway will automatically deploy
2. Wait 2-3 minutes for deployment
3. You'll get a URL like: `https://procurement-copilot-production-abc123.up.railway.app`
4. **WRITE DOWN THIS URL** - you'll need it for DNS!

### Step 6: Test Your Deployed API
```bash
# Test health (replace with your Railway URL)
curl https://your-railway-url.up.railway.app/api/v1/health

# Test tenders data
curl https://your-railway-url.up.railway.app/api/v1/tenders/tenders?limit=5

# Should return JSON with your 200 tenders!
```

### Step 7: Add Custom Domain
1. In Railway project, go to **"Settings"** → **"Domains"**
2. Click **"Custom Domain"**
3. Enter: `api.tenderpulse.eu`
4. Railway will show you DNS instructions

### Step 8: Configure DNS
1. Go to your domain provider (where you bought tenderpulse.eu)
2. Add DNS record:
   - **Type**: CNAME
   - **Name**: api
   - **Value**: [your-railway-url].up.railway.app

### Step 9: Verify Everything Works
```bash
# After DNS propagates (5-30 minutes):
curl https://api.tenderpulse.eu/api/v1/health
curl https://api.tenderpulse.eu/api/v1/tenders/tenders?limit=5

# Should return your 200 tenders with €800M+ value!
```

## 🎉 SUCCESS!

Once deployed, you'll have:
- ✅ **API URL**: https://api.tenderpulse.eu
- ✅ **200+ Active Tenders** worth €800M+
- ✅ **Production-ready** with health checks
- ✅ **EU hosting** on Railway
- ✅ **Ready for customers**

## 🔧 If You Get Stuck:

### Railway Deployment Fails:
- Check the **"Deployments"** tab for error logs
- Make sure `railway_deploy.py` is in the root directory
- Verify `requirements.txt` includes all dependencies

### API Returns Errors:
- Check **"Logs"** tab in Railway dashboard
- Verify environment variables are set correctly
- Test the health endpoint first: `/api/v1/health`

### DNS Not Working:
- DNS can take up to 48 hours to propagate
- Test with the direct Railway URL first
- Use `dig api.tenderpulse.eu` to check DNS status

## 📞 Next Steps After Deployment:
1. Deploy frontend to Vercel (using the API URL)
2. Configure Stripe payments
3. Set up Resend for emails
4. Start customer acquisition!

---

**Your TenderPulse API is ready to serve customers with 200+ active EU procurement opportunities worth €800M+!** 🚀

Start with Step 1 above - the entire deployment should take 15-30 minutes.
