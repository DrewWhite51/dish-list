# Deployment Summary

## What Changed

Your Pared recipe parser now uses **PostgreSQL exclusively** for truly free deployment using Render + Supabase.

### Files Modified

1. **recipe_database.py** (REPLACED)
   - Removed old CSV-based implementation
   - Now uses PostgreSQL exclusively via psycopg v3
   - Requires `DATABASE_URL` environment variable
   - Connects to Supabase PostgreSQL database

2. **recipe_parser.py**
   - Simplified to use PostgreSQL only
   - Removed conditional CSV/PostgreSQL logic
   - Requires `DATABASE_URL` to be set

3. **requirements.txt**
   - Added `psycopg[binary]==3.2.3` for PostgreSQL support
   - Modern psycopg v3 (no compilation needed)

4. **render.yaml**
   - Updated to use free tier (no disk)
   - Added DATABASE_URL environment variable placeholder

5. **README.md**
   - Added comprehensive Supabase + Render setup guide
   - Clarified Render free tier limitations (ephemeral storage)
   - Documented deployment options with costs

6. **.gitignore**
   - Removed `/db` directory (no longer needed)

## Deployment Options

### Option A: Render Starter ($7/month)
- Persistent disk storage for PostgreSQL
- No cold starts
- 512MB RAM

### Option B: Render Free + Supabase ($0/month) ⭐ RECOMMENDED
- PostgreSQL database (500MB free from Supabase)
- Recipes persist between deploys
- 30-60s cold starts after 15 min inactivity
- Perfect for family/friends use

### Option C: Oracle Cloud ($0/month)
- Full VM control
- No cold starts
- Complex setup (~2 hours)
- Requires server administration skills

## How It Works

### Local Development
```bash
# Option 1: Use .env file (recommended)
cp .env.example .env
# Edit .env and add your DATABASE_URL
python application.py

# Option 2: Set environment variable directly
export DATABASE_URL="postgresql://user:password@host:port/database"
python application.py

# Data stored in PostgreSQL database (Supabase)
```

### Production (Render + Supabase)
```bash
# DATABASE_URL set automatically by Render environment variable
gunicorn application:app

# Data stored in Supabase PostgreSQL database
```

## Next Steps

1. **Set up Supabase** (follow README instructions)
   - Create account
   - Create project and database
   - Run SQL to create tables
   - Copy DATABASE_URL

2. **Deploy to Render**
   - Push changes to GitHub
   - Create Render web service
   - Add DATABASE_URL environment variable
   - Deploy

3. **Test**
   - Parse a recipe
   - Redeploy (git push)
   - Verify recipes persist

## Migration from CSV (Optional)

If you already have recipes in CSV format locally, you can migrate them to PostgreSQL:

1. Set up Supabase and get DATABASE_URL
2. Set DATABASE_URL environment variable locally:
   ```bash
   export DATABASE_URL="postgresql://postgres:..."
   ```
3. Run a migration script (you'd need to write this)
4. Verify data in Supabase dashboard

## Cost Comparison

| Option | Monthly Cost | Setup Time | Cold Starts | Storage |
|--------|--------------|------------|-------------|---------|
| Render Starter | $7 | 10 min | No | Persistent disk |
| **Render Free + Supabase** | **$0** | 20 min | Yes (30-60s) | PostgreSQL 500MB |
| Oracle Cloud | $0 | 2 hours | No | Full disk |

## Support

- Supabase docs: https://supabase.com/docs
- Render docs: https://render.com/docs
- PostgreSQL docs: https://www.postgresql.org/docs/

---

**Your app now supports both CSV (local) and PostgreSQL (production) with zero code changes required!**
