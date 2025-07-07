from langchain.prompts import PromptTemplate
import httpx

import httpx

import os
from dotenv import load_dotenv
from groq import Groq
import httpx

# Load environment variables from .env file
load_dotenv()

# Get keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY")

# http_client = httpx.Client()  # or AsyncClient() if async

http_client = httpx.Client(verify=False)



CART_EXTRACTION_PROMPT = PromptTemplate.from_template("""
You are an intelligent assistant that extracts food order items from customer messages.

Given a menu and a user message, return a structured JSON list of the items the user wants to add to their cart. Each item should include the dish name and quantity.

### Menu:
{menu}

### User message:
{message}

### JSON Output format:
[
  {{
    "item": "<dish name from the menu>",
    "quantity": <integer>
  }},
  ...
]

Only include items from the menu. If none match, return an empty list.
""")
