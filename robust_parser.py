"""
Recipe parsing using GPT-4o-mini for robust extraction
"""
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def parse_recipe_robust(url):
    """
    Parse recipe using GPT-4o-mini for robust extraction.

    This approach uses an LLM instead of brittle HTML parsing,
    making it work reliably across virtually all recipe websites.

    Cost: ~$0.001-0.002 per recipe (less than a penny)
    """
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        # Parse HTML and extract clean text
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove non-content elements (scripts, styles, navigation, etc.)
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)

        # Truncate if too long (GPT-4o-mini has token limits)
        # 15000 chars ≈ 3750 tokens, well under the 128k limit
        if len(text) > 15000:
            text = text[:15000]

        # Get OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                "error": "OPENAI_API_KEY not set in environment variables",
                "title": "",
                "ingredients": [],
                "directions": [],
                "source_url": url
            }

        # Call GPT-4o-mini with structured output
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a recipe extraction assistant. Extract recipe information from webpage text and return it as JSON.

Return ONLY valid JSON with this exact structure:
{
  "title": "recipe name here",
  "ingredients": ["ingredient 1", "ingredient 2", ...],
  "directions": ["step 1", "step 2", ...],
  "prep_time": "15 minutes",
  "cook_time": "30 minutes"
}

Rules:
- Extract the complete recipe title
- List ALL ingredients as separate items in the array
- List ALL cooking steps/directions as separate items in the array
- Extract prep_time and cook_time if found in the recipe. If not explicitly stated, provide reasonable estimates based on the recipe complexity
- Format times as "X minutes" or "X hours Y minutes" (e.g., "15 minutes", "1 hour 30 minutes")
- Preserve the order of ingredients and directions
- If you cannot find a field, use empty string ("") or empty array ([])
- Do not add any extra fields beyond the ones shown above
- Do not include any text outside the JSON object"""
                },
                {
                    "role": "user",
                    "content": f"Extract the recipe from this webpage text:\n\n{text}"
                }
            ],
            temperature=0,  # Deterministic output
            response_format={"type": "json_object"}  # Ensure valid JSON
        )

        # Parse the GPT response
        result = json.loads(completion.choices[0].message.content)

        # Validate and clean the result
        title = result.get("title", "").strip()
        ingredients = result.get("ingredients", [])
        directions = result.get("directions", [])
        prep_time = result.get("prep_time", "").strip()
        cook_time = result.get("cook_time", "").strip()

        # Ensure they're lists
        if not isinstance(ingredients, list):
            ingredients = []
        if not isinstance(directions, list):
            directions = []

        # Clean up strings
        ingredients = [str(i).strip() for i in ingredients if i and str(i).strip()]
        directions = [str(d).strip() for d in directions if d and str(d).strip()]

        return {
            "title": title or "Untitled Recipe",
            "ingredients": ingredients,
            "directions": directions,
            "prep_time": prep_time,
            "cook_time": cook_time,
            "source_url": url
        }

    except requests.exceptions.HTTPError as e:
        return {
            "error": f"HTTP Error: Could not access recipe (Status {e.response.status_code})",
            "title": "",
            "ingredients": [],
            "directions": [],
            "prep_time": "",
            "cook_time": "",
            "source_url": url
        }
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out - website took too long to respond",
            "title": "",
            "ingredients": [],
            "directions": [],
            "prep_time": "",
            "cook_time": "",
            "source_url": url
        }
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse GPT response as JSON: {str(e)}",
            "title": "",
            "ingredients": [],
            "directions": [],
            "prep_time": "",
            "cook_time": "",
            "source_url": url
        }
    except Exception as e:
        return {
            "error": f"Parsing error: {str(e)}",
            "title": "",
            "ingredients": [],
            "directions": [],
            "prep_time": "",
            "cook_time": "",
            "source_url": url
        }
