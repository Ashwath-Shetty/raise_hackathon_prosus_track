import json
import re
from datetime import datetime
from difflib import get_close_matches
from langchain.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from models import Restaurant, MenuItem, CartItem, UserProfile, KnowledgeGraph
from tools import LocationNormalizerTool, RestaurantSearchTool, MenuTool
from utils import normalize
from prompts import CART_EXTRACTION_PROMPT, GROQ_API_KEY, http_client
from typing import List, Optional



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

