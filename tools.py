import json
import re
import requests
from typing import List, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from models import Restaurant
from prompts import GROQ_API_KEY, SERP_API_KEY, http_client

class LocationNormalizerInput(BaseModel):
    user_message: str = Field(description="User's raw location message")

class LocationNormalizerTool(BaseTool):
    name: str = "location_normalizer"
    description: str = "Convert user location input into a clean location string suitable for search"
    args_schema: Type[BaseModel] = LocationNormalizerInput

    def _run(self, user_message: str) -> dict:
        prompt = f"""
    You are a helpful assistant that takes messy or informal location input and converts it into a clean, globally recognized location string.
    
    Respond ONLY with JSON in this format:
    {{
        "location": "Koramangala, Bengaluru, India",
        "ll": "12.9352,77.6245"
    }}
    
    Input: "{user_message}"
    """
        llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192", temperature=0.2,http_client=http_client)
        response = llm.invoke(prompt)
    
        # ✅ Convert to plain string if needed
        if hasattr(response, "content"):
            response = response.content
    
        try:
            json_str = re.search(r'\{.*\}', response, re.DOTALL).group()
            return json.loads(json_str)
        except Exception as e:
            print(f"[LLM LocationNormalizer Error]: {e}")
            return {"location": user_message.title()}

    def _arun(self, user_message: str):
        raise NotImplementedError("Async not supported")



class RestaurantSearchInput(BaseModel):
    location: str = Field(description="User's location or lat,long")
    food_type: str = Field(default="", description="Type of food (optional)")

class RestaurantSearchTool(BaseTool):
    name: str = "restaurant_search"
    description: str = "Search for restaurants based on location and food type"
    args_schema: Type[BaseModel] = RestaurantSearchInput

    def _run(self, location: str, food_type: str = "") -> str:
        try:
            mock_restaurants = self._generate_restaurants(location, food_type)
            if not mock_restaurants:
                return f"❌ No '{food_type}' restaurants found near {location}."

            result = f"🍽️ Top {min(3, len(mock_restaurants))} restaurants found for '{food_type}' in {location}:\n\n"
            for i, r in enumerate(mock_restaurants[:3], 1):
                stars = "⭐" * int(r.rating) if r.rating > 0 else "No rating"
                result += f"{i}. **{r.name}**\n"
                result += f"   📍 {r.address}\n"
                result += f"   🍴 {r.cuisine_type}\n"
                result += f"   {stars} ({r.rating}/5)\n\n"
            return result

        except Exception as e:
            print(f"[RestaurantSearch Error]: {e}")
            return f"⚠️ Error searching for restaurants near {location}."

    def _generate_restaurants(self, location: str, food_type: str = "") -> List[Restaurant]:
        try:
            # Force usage of location string; lat/long often fails outside the US
            query = f"{food_type} restaurants in {location}"
            params = {
                "engine": "google_maps",
                "type": "search",
                "q": query,
                "location": location,
                "api_key": SERP_API_KEY
            }
    
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
    
            results = []
            for place in data.get("local_results", [])[:5]:
                results.append(
                    Restaurant(
                        name=place.get("title", "Unknown"),
                        address=place.get("address", "Unknown"),
                        rating=float(place.get("rating", 0.0)),
                        cuisine_type=food_type,
                        phone=place.get("phone", "")
                    )
                )
            return results
        except Exception as e:
            print("SerpAPI error:", e)
            return []


    def _arun(self, location: str, food_type: str = ""):
        raise NotImplementedError("Async not implemented")



#####

class MenuInput(BaseModel):
    restaurant_name: str = Field(description="Name of the restaurant")
    cuisine_type: str = Field(description="Type of cuisine the restaurant serves")

class MenuTool(BaseTool):
    name: str = "get_menu"
    description: str = "Get menu for a specific restaurant based on its cuisine type"
    args_schema: Type[BaseModel] = MenuInput

    def _run(self, restaurant_name: str, cuisine_type: str) -> str:
        try:
            prompt = f"""
                        You're an expert menu designer. Create a realistic and appealing menu for a restaurant named "{restaurant_name}".
                        Cuisine: {cuisine_type}
                        Generate 4–6 menu items. For each item, include:
                        
                        - Dish name
                        - Short 1-line description
                        - Price (in USD, $5–$20)
                        - Category (e.g., Appetizer, Main Course, Dessert)
                        
                        Respond in this format only:
                        Dish Name | Price | Category | Description
                        
                        Example:
                        Margherita Pizza | $12.99 | Main Course | Classic tomato, mozzarella, and basil on sourdough crust.
                        """

            llm = ChatGroq(
                temperature=0.3,
                groq_api_key=GROQ_API_KEY,
                model_name="llama3-8b-8192",
                http_client=http_client
            )

            result = llm.invoke(prompt)
            raw_structured = result.content.strip()
            formatted = self._format_llm_menu(raw_structured, restaurant_name)
            return formatted, raw_structured

        except Exception as e:
            print(f"[MenuTool LLM Error]: {e}")
            return "Sorry, I couldn't generate the menu at the moment. Please try again later."


    def _format_llm_menu(self, raw_output: str, restaurant_name: str) -> str:
        lines = [line.strip() for line in raw_output.strip().split("\n") if line.strip()]
        result = f"🍽️ Menu for {restaurant_name}:\n\n"
    
        categories = {}
        for line in lines:
            # Skip header or lines that don't have exactly 4 parts
            if line.lower().startswith("dish name") or line.count("|") != 3:
                continue
            try:
                name, price, category, desc = [part.strip() for part in line.split("|")]
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, price, desc))
            except Exception as e:
                print("[Menu Parse Error]:", e, "Line:", line)
    
        for cat, items in categories.items():
            result += f"📂 {cat}\n"
            for name, price, desc in items:
                result += f"   • {name} - {price}\n"
                result += f"     {desc}\n\n"
    
        result += "💡 To add items to your cart, say something like:\n"
        result += "   'Add 2 Margherita Pizza' or 'I want the Caesar Salad'"
        return result






