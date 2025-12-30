from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This allows local development with .env file
# In production (Render), environment variables are set directly
load_dotenv()

from recipe_parser import app

if __name__ == "__main__":
    app.run()