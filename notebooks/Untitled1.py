#!/usr/bin/env python
# coding: utf-8

# In[1]:


from groq import Groq
import httpx
import json


# In[2]:


MODEL = "llama3-70b-8192" # "llama-3.3-70b-versatile" #
response_format={"type": "json_object"}
seed = 42
temperature=0
top_p = 1e-5


# In[3]:


import os
import json
import gradio as gr
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from difflib import get_close_matches

# Configuration
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Set your Groq API key
GROQ_API_KEY = 
SERP_API_KEY = 

cert = "/Users/shettyra/Downloads/ZscalerRootCerts_2/ZscalerRootCertificate-2048-SHA256.crt" 
# http_client = httpx.Client(verify=False)
http_client=httpx.Client(verify=cert)
# client = Groq(api_key=,http_client=http_client)

# Data Models
@dataclass
class Restaurant:
    name: str
    address: str
    rating: float
    cuisine_type: str
    phone: str = ""

@dataclass
class MenuItem:
    name: str
    price: float
    description: str
    category: str

@dataclass
class CartItem:
    item: MenuItem
    quantity: int

@dataclass
class UserProfile:
    user_id: str
    preferred_cuisines: List[str]
    favorite_restaurants: List[str]
    order_history: List[dict]
    location: str = ""

# Knowledge Graph (Simple JSON storage)
class KnowledgeGraph:
    def __init__(self):
        self.users = {}
        self.restaurants = {}
        self.orders = {}
    
    def add_user(self, user_profile: UserProfile):
        self.users[user_profile.user_id] = asdict(user_profile)
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        if user_id in self.users:
            data = self.users[user_id]
            return UserProfile(**data)
        return None
    
    def update_user_preferences(self, user_id: str, cuisine: str, restaurant: str):
        if user_id not in self.users:
            self.users[user_id] = asdict(UserProfile(user_id, [], [], []))
        
        user_data = self.users[user_id]
        if cuisine not in user_data['preferred_cuisines']:
            user_data['preferred_cuisines'].append(cuisine)
        if restaurant not in user_data['favorite_restaurants']:
            user_data['favorite_restaurants'].append(restaurant)



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








####




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


import unicodedata
import re

import unicodedata
import re

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)  # normalize spaces
    return text.strip()






# In[4]:


class KnowledgeGraph:
    def __init__(self):
        self.users = {}
        self.restaurants = {}
        self.orders = {}
    
    def add_user(self, user_profile: UserProfile):
        self.users[user_profile.user_id] = asdict(user_profile)
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        if user_id in self.users:
            data = self.users[user_id]
            return UserProfile(**data)
        return None
    
    def update_user_preferences(self, user_id: str, cuisine: str, restaurant: str):
        if user_id not in self.users:
            self.users[user_id] = asdict(UserProfile(user_id, [], [], []))
        
        user_data = self.users[user_id]
        if cuisine not in user_data['preferred_cuisines']:
            user_data['preferred_cuisines'].append(cuisine)
        if restaurant not in user_data['favorite_restaurants']:
            user_data['favorite_restaurants'].append(restaurant)

    def debug_view(self):
        print("\n=== KNOWLEDGE GRAPH STATE ===")
        print("📌 Users:")
        pprint.pprint(self.users)
        print("\n📌 Restaurants:")
        pprint.pprint(self.restaurants)
        print("\n📌 Orders:")
        pprint.pprint(self.orders)
        print("=============================\n")



import re
# Food Ordering Agent
class FoodOrderingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=GROQ_API_KEY,
            model_name="llama3-8b-8192",
            http_client=http_client
        )
        
        self.knowledge_graph = KnowledgeGraph()
        self.current_user_id = "user_001"  # Simple user ID for demo
        self.current_location = ""
        self.current_cuisine = ""
        self.selected_restaurant = ""
        self.cart = []
        self.conversation_state = "greeting"
        self.raw_menu_text = ""
        self.structured_menu_text = ""

        
        # Memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True
        )
        
        # Tools
        self.tools = [
            LocationNormalizerTool(),
            RestaurantSearchTool(),
            MenuTool()
        ]
        
        # Agent prompt
        self.agent_prompt = PromptTemplate.from_template("""
        You are a helpful food ordering assistant. Follow these stages:
        
        1. GREETING: Welcome the user warmly
        2. LOCATION: Ask for user's location
        3. FOOD_PREFERENCE: Ask what type of food they want
        4. RESTAURANT_SEARCH: Use restaurant_search tool to find restaurants
        5. RESTAURANT_SELECTION: Help user select a restaurant
        6. MENU_DISPLAY: Use get_menu tool to show menu
        7. ORDER_TAKING: Help user add items to cart
        8. ORDER_CONFIRMATION: Confirm the order
        9. ORDER_PROCESSING: Process the order
        
        Current conversation state: {state}
        User location: {location}
        Selected restaurant: {restaurant}
        Current cart: {cart}
        
        Tools available: {tools}
        
        Previous conversation:
        {chat_history}
        
        Human: {input}
        
        Remember to:
        - Be friendly and helpful
        - Ask one question at a time
        - Use tools when needed
        - Keep track of the conversation flow
        - Confirm details before proceeding
        
        Assistant:
        """)

    def parse_llm_menu(self, menu_text: str) -> List[MenuItem]:
        """Parse LLM-formatted menu into structured MenuItem objects"""
        items = []
        lines = [line.strip() for line in menu_text.split("\n") if line.strip()]
        for line in lines:
            if line.lower().startswith("dish name") or line.count("|") != 3:
                continue
            try:
                # name, price, category, desc = [part.strip() for part in line.split("|")]
                raw_name, price, category, desc = [part.strip() for part in line.split("|")]
                # Remove numbering prefix like "1. " from dish name
                # name = re.sub(r"^\d+\.\s*", "", raw_name)
                name = re.sub(r"^[•\-\d\. ]+", "", raw_name)

                
                price_float = float(price.replace("$", "").strip())
                items.append(MenuItem(name=name, price=price_float, description=desc, category=category))
            except Exception as e:
                print(f"[Menu Parse Error]: {e} -- Line: {line}")
        return items

    
    def process_message(self, message: str) -> str:
        """Process user message and return response"""
        try:
            response = ""

            if any(kw in message.lower() for kw in ["cart", "show cart", "view cart"]):
                response = self.get_cart_summary()
                # Log memory (optional)
                self.memory.chat_memory.add_user_message(message)
                self.memory.chat_memory.add_ai_message(response)
                return response
            
            # Simple state machine logic
            if self.conversation_state == "greeting":
                response = "Hello! Welcome to our food ordering service!  I'm here to help you find and order delicious food. What's your location so I can find restaurants near you?"
                self.conversation_state = "location"
                
            # elif self.conversation_state == "location":
            #     self.current_location = message.strip()
            #     response = f"Great! I've set your location to {self.current_location}. What type of food are you craving today? (e.g., pizza, burgers, sushi, etc.)"
            #     self.conversation_state = "food_preference"

            elif self.conversation_state == "location":
                try:
                    loc_tool = LocationNormalizerTool()
                    norm = loc_tool._run(message.strip())
                    self.current_location = norm.get("location", message.strip().title())
                    response = f"Great! I've set your location to {self.current_location}. What type of food are you craving today? (e.g., pizza, burgers, sushi, etc.)"
                    self.conversation_state = "food_preference"
                except Exception as e:
                    print("Location normalization failed:", e)
                    print("Location normalization failed:", e)
                    self.current_location = message.strip().title()
                    response = f"Okay, I've set your location to **{self.current_location}**. Now tell me what you're craving!"
                    self.conversation_state = "food_preference"  # 👈 Advance state even in fallback
                    # normalizer = LocationNormalizerTool()
                #     result = normalizer._run(message)
                #     self.current_location = result.get("location", message.title())
                #     response = f"Great! I've set your location to **{self.current_location}**. What type of food are you craving today? (e.g., pizza, burgers, sushi, etc.)"
                #     self.conversation_state = "food_preference"
                # except Exception as e:
                #     print("Location normalization failed:", e)
                #     self.current_location = message.strip().title()
                #     response = f"Okay, I've set your location to **{self.current_location}**. Now tell me what you're craving!"
                #     self.conversation_state = "food_preference"

                
            elif self.conversation_state == "food_preference":
                self.current_cuisine = message.strip()
                # Use restaurant search tool
                search_tool = RestaurantSearchTool()
                restaurants = search_tool._run(self.current_location, self.current_cuisine)
                response = f"{restaurants}\nWhich restaurant would you like to order from? Just tell me the name or number."
                self.conversation_state = "restaurant_selection"
                
            elif self.conversation_state == "restaurant_selection":
                # Parse restaurant selection
                selection = message.strip().lower()

                print(selection,self.current_cuisine)
                
                # Get the list of generated restaurants
                search_tool = RestaurantSearchTool()
                mock_restaurants = search_tool._generate_restaurants(self.current_location, self.current_cuisine)
                
                # Match selection to restaurant
                selected_index = None
                for i, restaurant in enumerate(mock_restaurants, 1):
                    name = restaurant.name.lower()
                
                    if str(i) == selection:
                        selected_index = i - 1
                        break
                    elif selection in name:  # 👈 allows partial match like "chianti"
                        selected_index = i - 1
                        break
                # for i, restaurant in enumerate(mock_restaurants, 1):
                #     if str(i) in selection or restaurant.name.lower() in selection:
                #         selected_index = i - 1
                #         break
                
                if selected_index is not None:
                    self.selected_restaurant = mock_restaurants[selected_index].name
                    cuisine_type = mock_restaurants[selected_index].cuisine_type
                    
                    # Get menu
                    

                    
                    menu_tool = MenuTool()
                    # raw_menu = menu_tool._run(self.selected_restaurant, cuisine_type)
                    # self.raw_menu_text = raw_menu  

                    formatted_menu, structured_menu = menu_tool._run(self.selected_restaurant, cuisine_type)
                    self.raw_menu_text = formatted_menu
                    self.structured_menu_text = structured_menu  # 👈 save this for parsing later

                    
                    # menu = menu_tool._run(self.selected_restaurant, cuisine_type)
                    response = f"Excellent choice! Here's the menu for {self.selected_restaurant}:\n\n{formatted_menu}\n\nWhat would you like to add to your cart? You can say something like 'Add 2 Margherita Pizza' or 'I want the Caesar Salad'."
                    self.conversation_state = "ordering"
                else:
                    response = "I didn't catch that. Please select one of the restaurants listed above."
                
            
            elif self.conversation_state == "ordering":
                if any(k in message.lower() for k in ["add", "want", "order"]):
                    # Call LLM to parse cart items
                    cart_extractor_prompt = CART_EXTRACTION_PROMPT.format(
                        menu=self.raw_menu_text,
                        message=message
                    )
                    llm_response = self.llm.invoke(cart_extractor_prompt)
                    raw_json_text = llm_response.content
                    cleaned_json = re.search(r"\[.*\]", raw_json_text, re.DOTALL)
                    if cleaned_json:
                        raw_json_text = cleaned_json.group(0)

                    try:
                        extracted_items = json.loads(raw_json_text)
                    except Exception as e:
                        print("Failed to parse JSON:", e)
                        extracted_items = []

                    print("LLM Extracted Cart JSON:", llm_response)
                    print("extracted_items",extracted_items)

                    
                    # try:
                    #     extracted_items = json.loads(llm_response)
                    # except Exception as e:
                    #     print("Failed to parse JSON:", e)
                    #     extracted_items = []
            
                    # menu_items = self.parse_llm_menu(self.raw_menu_text)
                    menu_items = self.parse_llm_menu(self.structured_menu_text)
                    print("Parsed Menu Items:", [m.name for m in menu_items])


                    # menu_lookup = {item.name.lower(): item for item in menu_items}
                    menu_lookup = {normalize(item.name): item for item in menu_items}

                    print("menu items, menu look up", menu_items,menu_lookup)
            
                    added = []
                    unmatched = []
                    for entry in extracted_items:
                        
                        name = normalize(entry["item"])
                        matched = menu_lookup.get(name)
                        quantity = entry.get("quantity", 1)

                        print(f"User requested item: {entry['item']} — matched to: {matched.name if matched else 'None'}")
                        # print(f"User requested item: {entry['item']} — matched to: {matched.name if matched else None}")


                        if not matched:
                            close = get_close_matches(name, list(menu_lookup.keys()), n=1, cutoff=0.5)
                            if close:
                                matched = menu_lookup[close[0]]

                        if matched:
                            self.cart.append(CartItem(matched, quantity))
                            added.append(f"{quantity} x {matched.name}")
                        else:
                            print(f"Unmatched item: {entry['item']}")
                            unmatched.append(entry["item"])
                        
                        # quantity = entry.get("quantity", 1)
                        # if name in menu_lookup:
                        #     self.cart.append(CartItem(menu_lookup[name], quantity))
                        #     added.append(f"{quantity} x {menu_lookup[name].name}")
            
                    

                    if added:
                        cart_summary = self.get_cart_summary()
                        response = f"🛒 Added to cart:\n- " + "\n- ".join(added) + f"\n\n{cart_summary}\n\nWould you like to add more or checkout?"
                        if unmatched:
                            response += "\n\n🚫 The following items were not found on the menu and were **not** added to your cart:\n- " + "\n- ".join(unmatched)
                        
                        # response += f"\n\n{cart_summary}\n\nWould you like to add more or checkout?"


                    else:
                        response = f"🚫 None of those items were found on the menu. Here's the menu again:\n\n{self.raw_menu_text}"
            
                # elif "checkout" in message.lower():
                #     if self.cart:
                #         cart_summary = self.get_cart_summary()
                #         response = f"🧾 Order Summary:\n\n{cart_summary}\n\nWould you like to confirm your order? (yes/no)"
                #         self.conversation_state = "confirmation"
                #     else:
                #         response = "🛒 Your cart is empty. Add some items first!"

                elif any(k in message.lower() for k in ["remove", "delete"]):
                    
                    # Try to parse what to remove
                    to_remove = re.findall(r"\d*\s*\w+", message.lower())
                    removed = []
                    for entry in to_remove:
                        parts = entry.strip().split()
                        if len(parts) == 2:
                            qty_text, item_text = parts
                        else:
                            qty_text = "1"
                            item_text = parts[0]
                        
                        try:
                            quantity = int(qty_text)
                        except ValueError:
                            quantity = 1
                
                        item_name = normalize(item_text)
                        match_found = False
                        for cart_item in self.cart:
                            if normalize(cart_item.item.name) == item_name:
                                if cart_item.quantity <= quantity:
                                    self.cart.remove(cart_item)
                                else:
                                    cart_item.quantity -= quantity
                                removed.append(f"{quantity} x {cart_item.item.name}")
                                match_found = True
                                break
                        
                        if not match_found:
                            cart_lookup = {normalize(ci.item.name): ci for ci in self.cart}
                            close = get_close_matches(item_name, list(cart_lookup.keys()), n=1, cutoff=0.6)
                            
                            if close:
                                matched_cart_item = cart_lookup[close[0]]
                                if matched_cart_item.quantity <= quantity:
                                    self.cart.remove(matched_cart_item)
                                else:
                                    matched_cart_item.quantity -= quantity
                                removed.append(f"{quantity} x {matched_cart_item.item.name}")
                                match_found = True
                            else:
                                print(f"No matching item found in cart for: {item_name}")
                    
                    if removed:
                        cart_summary = self.get_cart_summary()
                        response = f"🗑️ Removed from cart:\n- " + "\n- ".join(removed) + f"\n\n{cart_summary}\n\nWould you like to add more or checkout?"
                    else:
                        response = f"⚠️ Couldn't find those items in your cart. Try using the item names as shown in the menu."


            
                elif "checkout" in message.lower() or "done" in message.lower():
                    if self.cart:
                        cart_summary = self.get_cart_summary()
                        response = f"Perfect! Here's your order summary:\n\n{cart_summary}\n\nWould you like to confirm this order? (yes/no)"
                        self.conversation_state = "confirmation"
                    else:
                        response = "Your cart is empty. Please add some items first!"
                
                    # else:
                    #     response = "I can help you add items to your cart. Try saying 'Add [item name]' or 'checkout' when you're ready."

                    
            elif self.conversation_state == "confirmation":
                if "yes" in message.lower():
                    order_id = self.process_order()
                    response = f"🎉 Order confirmed! Your order #{order_id} has been placed successfully.\n\nDelivery time: 30-45 minutes\nRestaurant: {self.selected_restaurant}\nTotal: ${self.get_total():.2f}\n\nThank you for your order! You'll receive updates via SMS."
                    self.save_user_preferences()
                    self.reset_conversation()
                else:
                    response = "No problem! You can continue adding items or modify your order. What would you like to do?"
                    self.conversation_state = "ordering"

            
                # return response


            
            else:
                response = "I'm here to help you order food! Would you like to start a new order?"
                self.conversation_state = "greeting"
            
            # Add to memory
            self.memory.chat_memory.add_user_message(message)
            self.memory.chat_memory.add_ai_message(response)
            
            return response
            
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Let's start over - what's your location?"
    
    def get_cart_summary(self) -> str:
        """Get formatted cart summary"""
        if not self.cart:
            return "Your cart is empty."
        
        summary = f"🛒 Your Cart ({self.selected_restaurant}):\n"
        total = 0
        for cart_item in self.cart:
            item_total = cart_item.item.price * cart_item.quantity
            summary += f"- {cart_item.quantity}x {cart_item.item.name}: ${item_total:.2f}\n"
            total += item_total
        
        summary += f"\n💰 Total: ${total:.2f}"
        return summary
    
    def get_total(self) -> float:
        """Calculate total cart value"""
        return sum(item.item.price * item.quantity for item in self.cart)
    
    def process_order(self) -> str:
        """Process the order"""
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save order to knowledge graph
        order_data = {
            "order_id": order_id,
            "user_id": self.current_user_id,
            "restaurant": self.selected_restaurant,
            "items": [{"name": item.item.name, "quantity": item.quantity, "price": item.item.price} for item in self.cart],
            "total": self.get_total(),
            "timestamp": datetime.now().isoformat(),
            "location": self.current_location
        }
        
        self.knowledge_graph.orders[order_id] = order_data
        print(f"✅ Order added to Knowledge Graph: {order_id}")
        self.knowledge_graph.debug_view()
        
        return order_id
    
    def save_user_preferences(self):
        """Save user preferences to knowledge graph"""
        if self.selected_restaurant:
            # Get cuisine type from generated restaurants
            search_tool = RestaurantSearchTool()
            mock_restaurants = search_tool._generate_restaurants(self.current_location, self.current_cuisine)
            current_restaurant = next((r for r in mock_restaurants if r.name == self.selected_restaurant), None)
            
            if current_restaurant:
                self.knowledge_graph.update_user_preferences(
                    self.current_user_id,
                    current_restaurant.cuisine_type,
                    self.selected_restaurant
                )
    
    def reset_conversation(self):
        """Reset for new conversation"""
        self.conversation_state = "greeting"
        self.current_location = ""
        self.current_cuisine = ""
        self.selected_restaurant = ""
        self.cart = []



# In[5]:


import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

def render_knowledge_graph(agent: FoodOrderingAgent) -> Image.Image:
    G = nx.DiGraph()

    # Add user node
    user_id = agent.current_user_id
    G.add_node(user_id, label="User", color="skyblue")

    # Add favorite restaurants and cuisines
    user = agent.knowledge_graph.get_user(user_id)
    if user:
        for cuisine in user.preferred_cuisines:
            G.add_node(cuisine, label="Cuisine", color="orange")
            G.add_edge(user_id, cuisine, label="likes cuisine")
        
        for rest in user.favorite_restaurants:
            G.add_node(rest, label="Restaurant", color="lightgreen")
            G.add_edge(user_id, rest, label="likes restaurant")

    # Add past orders
    for order_id, order in agent.knowledge_graph.orders.items():
        G.add_node(order_id, label="Order", color="gray")
        G.add_edge(user_id, order_id, label="placed")

        G.add_node(order["restaurant"], label="Restaurant", color="lightgreen")
        G.add_edge(order_id, order["restaurant"], label="from")

        for item in order["items"]:
            item_name = item["name"]
            G.add_node(item_name, label="Dish", color="pink")
            G.add_edge(order_id, item_name, label=f"{item['quantity']}x")

    pos = nx.spring_layout(G, seed=42)
    node_colors = [G.nodes[n].get("color", "white") for n in G.nodes()]

    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1000, font_size=8)
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): d["label"] for u, v, d in G.edges(data=True)})

    # Save to image
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return Image.open(buf)


# In[6]:


def create_chatbot_interface():
    agent = FoodOrderingAgent()
    
    def chat_fn(message, history):
        if not message.strip():
            return history, ""
        response = agent.process_message(message)
        history.append((message, response))
        return history, ""
    
    def reset_fn():
        agent.reset_conversation()
        return [], ""

    def show_kg_fn():
        img = render_knowledge_graph(agent)
        return img
    
    with gr.Blocks(title="Food Ordering Chatbot", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🍕 Food Ordering Chatbot")
        gr.Markdown("Welcome to our AI-powered food ordering service! I'll help you find restaurants and place orders.")

        chatbot = gr.Chatbot(value=[], height=500, show_label=False, show_copy_button=True)
        
        with gr.Row():
            msg = gr.Textbox(placeholder="Type your message here...", scale=4, show_label=False, container=False)
            send_btn = gr.Button("Send", scale=1, variant="primary")
            clear_btn = gr.Button("New Order", scale=1, variant="secondary")

        # Knowledge Graph button and viewer
        with gr.Row():
            show_kg_btn = gr.Button("Show Knowledge Graph", variant="secondary")
            kg_image = gr.Image(type="pil", label="Knowledge Graph")

        # Event handlers
        msg.submit(chat_fn, inputs=[msg, chatbot], outputs=[chatbot, msg])
        send_btn.click(chat_fn, inputs=[msg, chatbot], outputs=[chatbot, msg])
        clear_btn.click(reset_fn, outputs=[chatbot, msg])
        show_kg_btn.click(show_kg_fn, outputs=kg_image)

        # Instructions
        gr.Markdown("""
        ### How to use:
        1. **Start** by saying hi  
        2. **Share** your location - I live in Koramangala Bengaluru  
        3. **Tell me** what type of food you want - pizza 
        4. **Choose** from recommended restaurants - Pizza hut  
        5. **Add items** to your cart (e.g., "Add 2 Margherita Pizza") / you also have the option to delete item / show cart  
        6. **Say 'checkout'** when ready to place order  
        7. **Confirm** your order  
        8. **Click 'Show Knowledge Graph'** to visualize your preferences and orders  
        """)
    
    return demo


# In[8]:


# Main execution
import json
import pprint

def view_knowledge_graph():
    
    state = {
        "Users": agent.knowledge_graph.users,
        "Orders": agent.knowledge_graph.orders,
        "Restaurants": agent.knowledge_graph.restaurants
    }
    return json.dumps(state, indent=2)


if __name__ == "__main__":
    # Set up environment variables (you'll need to set these)
    if not GROQ_API_KEY:
        print("⚠️  Please set GROQ_API_KEY environment variable")
        print("   export GROQ_API_KEY='your_groq_api_key_here'")
    
    # Create and launch interface
    demo = create_chatbot_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=True  # Set to False for local only
    )


# In[9]:


demo.close()


# In[10]:


get_ipython().system('pip install pipreqs')


# In[11]:


get_ipython().system('pipreqs . --force')


# In[ ]:


# Gradio Interface
def create_chatbot_interface():
    agent = FoodOrderingAgent()
    
    def chat_fn(message, history):
        """Process chat message"""
        if not message.strip():
            return history, ""
        
        response = agent.process_message(message)
        history.append((message, response))
        return history, ""
    
    def reset_fn():
        """Reset conversation"""
        agent.reset_conversation()
        return [], ""
    
    # Create Gradio interface
    with gr.Blocks(title="Food Ordering Chatbot", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🍕 Food Ordering Chatbot")
        gr.Markdown("Welcome to our AI-powered food ordering service! I'll help you find restaurants and place orders.")
        
        chatbot = gr.Chatbot(
            value=[],
            height=500,
            show_label=False,
            show_copy_button=True
        )
        
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Type your message here...",
                scale=4,
                show_label=False,
                container=False
            )
            send_btn = gr.Button("Send", scale=1, variant="primary")
            clear_btn = gr.Button("New Order", scale=1, variant="secondary")
        
        # Event handlers
        msg.submit(
            chat_fn,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        send_btn.click(
            chat_fn,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )
        
        clear_btn.click(
            reset_fn,
            outputs=[chatbot, msg]
        )
        
        # Instructions
        gr.Markdown("""
        ### How to use:
        1. **Start** by saying hi
        2. **Share** your location - I live in Koramangala Bengaluru
        2. **Tell me** what type of food you want - Italian
        3. **Choose** from recommended restaurants - Pizza hut
        4. **Add items** to your cart (e.g., "Add 2 Margherita Pizza") / you also have the option to delete item / show cart
        5. **Say 'checkout'** when ready to place order
        6. **Confirm** your order
        
        ### Sample Commands:
        - "I'm in downtown Seattle"
        - "I want pizza"
        - "Add 2 Margherita Pizza"
        - "Checkout"
        """)
    
    return demo


