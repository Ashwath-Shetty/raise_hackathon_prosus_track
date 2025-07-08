from dataclasses import dataclass, asdict
from typing import List, Optional
import pprint



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


            