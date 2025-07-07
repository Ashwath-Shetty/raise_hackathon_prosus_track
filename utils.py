import unicodedata
import re
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
from models import UserProfile


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import FoodOrderingAgent
    


def normalize(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)  # normalize spaces
    return text.strip()

def render_knowledge_graph(agent) -> Image.Image:
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
