# Pared

Parse food recipes from URLs and create grocery lists.

## Features

- **Recipe Parsing**: Extracts ingredients and directions from recipe websites
- **Recipe Storage**: Save and manage your recipe collection
- **Search**: Find recipes by title
- **Modern UI**: Clean, responsive design with TailwindCSS v4
- **Lightweight**: Only 3 Python dependencies
- **Free Hosting**: Deploy on Oracle Cloud Free Tier ($0/month forever)

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install CSS dependencies and build styles
npm install
npm run build:css

# Run the app locally
python application.py
```

Access at `http://localhost:5000`

## Requirements

- Python 3.10+
- Flask, requests, beautifulsoup4
- Node.js (for TailwindCSS v4 build process)

## What You Can Do

- **Parse Recipes**: Enter any recipe URL to extract ingredients and directions
- **Save & Organize**: Build your recipe collection
- **Search**: Find recipes by title
- **Edit Recipes**: Modify saved recipes as needed
- **Copy Ingredients**: One-click copy to clipboard for grocery shopping

## Project Structure

```
ez-recipe/
├── application.py          # Entry point
├── recipe_parser.py        # Routes and parsing logic
├── recipe_database.py      # CSV storage
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies (TailwindCSS v4)
├── templates/              # HTML templates with TailwindCSS classes
├── static/
│   ├── globals.css         # TailwindCSS v4 source file with custom styles
│   └── output.css          # Compiled CSS (generated)
└── db/                     # Recipe storage (auto-created)
```

## Styling & Design

The application uses a modern design system powered by TailwindCSS v4 with:

- **Bold orange primary color** for energy and appetite appeal
- **Warm coral accents** for interactive elements
- **Clean minimalist base** with subtle grays
- **OKLCH color space** for vibrant, perceptually uniform colors
- **Responsive design** that works on mobile, tablet, and desktop

### Development Workflow

When making style changes:

```bash
# Watch for CSS changes during development
npm run watch:css

# Build for production (minified)
npm run build:css
```

## Deployment

### Render (Recommended - $1/month)

Deploy Pared on Render's managed platform for simple, hands-off hosting:

**What you get:**
- 512MB RAM (sufficient for Pared)
- Automatic Git deployments
- Free SSL certificates
- Built-in monitoring and logs
- **Note**: Free tier sleeps after 15min inactivity (30-60s cold start)

**Total Cost**: $1/month for persistent disk storage

---

#### Quick Deploy (10 minutes)

**1. Create Render Account**
- Go to https://render.com
- Sign up with GitHub (recommended) or email
- No credit card required for free tier

**2. Create New Web Service**
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select this repository
- Click "Connect"

**3. Configure Service**

Basic Settings:
- **Name**: `pared` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Runtime**: Detected automatically (Python 3)

Build & Deploy Commands:
- **Build Command**:
  ```
  pip install -r requirements.txt && npm install && npm run build:css && rm -rf node_modules
  ```
- **Start Command**:
  ```
  gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 2 application:app
  ```

**Instance Type**: Free (512MB RAM)

**4. Add Persistent Disk** ⚠️ **REQUIRED**

Without persistent storage, recipes will be deleted on each deploy!

- Scroll to "Disks" section
- Click "Add Disk"
- **Name**: `pared-recipes`
- **Mount Path**: `/opt/render/project/src/db`
- **Size**: 1 GB
- **Cost**: $1/month

**5. Deploy**
- Click "Create Web Service"
- Wait 3-5 minutes for build
- You'll get a URL: `https://pared-XXXX.onrender.com`

**6. Test**
- Visit your Render URL
- Parse a recipe
- Verify recipes persist after redeployment

---

#### Understanding Cold Starts

The free tier has trade-offs:

- Apps **sleep after 15 minutes** of inactivity
- First request after sleep takes **30-60 seconds** to wake up
- Subsequent requests are instant

**Who this works for:**
- Personal use / family & friends
- Apps used a few times per day
- Non-time-critical recipe lookups

**Avoid cold starts:**
- Upgrade to paid tier ($7/month) for no sleep
- Use uptime monitor to ping every 14 minutes (some free services available)

---

#### Automatic Deployments

Every git push automatically deploys:

```bash
git add .
git commit -m "Update recipe parser"
git push origin main

# Render automatically builds and deploys (2-4 minutes)
```

---

#### Monitoring & Logs

**View Logs:**
- Dashboard → Your Service → "Logs" tab
- Real-time streaming
- Search and filter available

**Metrics** (Free tier):
- CPU and memory usage
- Request count
- Response times

---

#### Backup Your Recipes

**Option 1: Via Render Shell**
- Dashboard → Your Service → "Shell" tab
- Run:
  ```bash
  cd /opt/render/project/src/db
  tar -czf backup.tar.gz *.csv
  ```
- Download from file browser

**Option 2: Git Commit** (if you don't gitignore `/db`)
```bash
git add db/*.csv
git commit -m "Backup recipes"
git push
```

---

#### Custom Domain (Optional)

**1. Add Domain in Render**
- Dashboard → Your Service → "Settings" → "Custom Domains"
- Click "Add Custom Domain"
- Enter `recipes.yourdomain.com` (or your domain)

**2. Configure DNS**

In your domain registrar (Namecheap, Cloudflare, etc.), add a CNAME record:

```
Type: CNAME
Name: recipes (or @ for root domain)
Value: pared-XXXX.onrender.com (from Render dashboard)
TTL: Auto or 300
```

**3. Wait for SSL**
- Render automatically provisions Let's Encrypt SSL
- Takes 5-15 minutes after DNS propagates
- Certificate auto-renews every 60 days

**4. Test**
Visit `https://recipes.yourdomain.com` - you should see your app with a valid SSL certificate!

---

### Alternative Platforms

Need different features? Here are alternatives:

| Platform | Monthly Cost | Setup Time | Cold Starts | Notes |
|----------|--------------|------------|-------------|-------|
| **Render Free** | **$1*** | 5 min | ✅ Yes (30-60s) | Recommended |
| Oracle Cloud | $0 | 2 hours | ❌ No | Free forever, manual setup |
| DigitalOcean | $5 | 10 min | ❌ No | Easiest managed option |
| Fly.io | $0-3 | 30 min | ❌ No | CLI-based, may have small overages |
| Railway | $5 | 10 min | ❌ No | Modern DX, usage-based billing |

*Requires $1/month persistent disk

For detailed comparison of all platforms, see the [deployment plan](/.claude/plans/glittery-nibbling-elephant.md).

## How It Works

The app uses HTML-based parsing to extract recipe data from websites. It looks for structured data (schema.org markup) and common recipe patterns to identify ingredients and cooking directions.

## License

MIT
