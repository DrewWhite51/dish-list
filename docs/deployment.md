# Deployment Guide

Deploy Dish List to production using Render.com and Supabase for free hosting.

## Prerequisites

- GitHub account
- Supabase account (free)
- Render.com account (free)
- OpenAI API key

## Deployment Options

### Recommended: Render Free + Supabase ($0/month)

- PostgreSQL database (500MB free from Supabase)
- Recipes persist between deploys
- 30-60s cold starts after 15 min inactivity
- Perfect for personal or family use

### Alternative: Render Starter ($7/month)

- No cold starts
- 512MB RAM
- Better performance for high traffic

## Step 1: Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to **Project Settings** → **Database**
4. Copy your **Connection String** (Pooler mode recommended)
5. The database tables will be created automatically by Flask-Migrate on first deployment

## Step 2: Prepare Your Repository

1. Push your code to GitHub
2. Ensure you have a `.env.example` file for reference
3. Verify `requirements.txt` includes all dependencies

## Step 3: Deploy to Render

1. Go to [render.com](https://render.com) and sign up
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: your-app-name
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && npm install && npm run build:css`
   - **Start Command**: `gunicorn application:app`
5. Add environment variables:
   - `DATABASE_URL`: Your Supabase connection string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: Generate a random secret key
6. Click **Create Web Service**

## Step 4: Run Database Migrations

After first deployment, you need to run migrations:

1. In Render dashboard, go to your web service
2. Click **Shell** tab
3. Run: `flask --app recipe_parser db upgrade`
4. Verify tables were created in Supabase dashboard

## Step 5: Verify Deployment

1. Visit your Render URL (e.g., `https://your-app.onrender.com`)
2. Test parsing a recipe
3. Verify the recipe appears in your Supabase database

## Environment Variables

Required environment variables for production:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string from Supabase | `postgresql://postgres:...@aws-0-us-east-1.pooler.supabase.com:6543/postgres` |
| `OPENAI_API_KEY` | OpenAI API key for recipe parsing | `sk-...` |
| `SECRET_KEY` | Flask secret key for sessions | Random string (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |

## Updating Your Deployment

To deploy updates:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

Render will automatically rebuild and redeploy your app.

## Troubleshooting

### Database Connection Error

Verify your `DATABASE_URL` is set correctly in Render environment variables. Make sure you're using the pooler connection string from Supabase.

### Migrations Not Applied

Run migrations manually via Render Shell:

```bash
flask --app recipe_parser db upgrade
```

### Cold Starts

On the free tier, your app will sleep after 15 minutes of inactivity. The first request after sleeping takes 30-60 seconds. This is expected behavior.

## Cost Breakdown

- **Render Free Tier**: $0/month (with cold starts)
- **Supabase Free Tier**: $0/month (500MB database)
- **OpenAI API**: ~$0.00045 per recipe parse
- **Total**: <$1/month for typical personal use
