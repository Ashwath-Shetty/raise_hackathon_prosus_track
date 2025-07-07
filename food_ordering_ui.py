"""
Food Ordering and Tracking Agent - Gradio UI
A simple interface for ordering food with chat functionality and cart management.
"""

import gradio as gr
import requests
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000/chat"
REQUEST_TIMEOUT = 10  # seconds

# Dummy data for demonstration
DUMMY_PAST_ORDERS = [
    {"id": "ORD-001", "date": "2024-07-05", "items": ["Pizza Margherita", "Coke"], "total": "$18.99"},
    {"id": "ORD-002", "date": "2024-07-04", "items": ["Burger", "Fries"], "total": "$14.50"},
    {"id": "ORD-003", "date": "2024-07-03", "items": ["Sushi Roll", "Miso Soup"], "total": "$22.75"}
]

# Global state for cart (in a real app, this would be stored in a database)
current_cart = []


def format_cart_display(cart: List[str]) -> str:
    """Format cart items for display in the UI."""
    if not cart:
        return "🛒 Your cart is empty"
    
    cart_text = "🛒 **Current Cart:**\n"
    for i, item in enumerate(cart, 1):
        cart_text += f"{i}. {item}\n"
    return cart_text


def format_past_orders(orders: List[Dict[str, Any]]) -> str:
    """Format past orders for display in the UI."""
    if not orders:
        return "📋 No past orders"
    
    orders_text = "📋 **Last 3 Orders:**\n"
    for order in orders:
        orders_text += f"• {order['id']} ({order['date']}) - {', '.join(order['items'])} - {order['total']}\n"
    return orders_text


def send_message_to_backend(message: str) -> str:
    """
    Send user message to the backend API and return the response.
    
    Args:
        message: User input message
        
    Returns:
        Agent response string
    """
    try:
        # Prepare request payload
        payload = {"message": message}
        
        # Send POST request to backend
        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        response_data = response.json()
        return response_data.get("response", "Sorry, I didn't understand that.")
        
    except requests.exceptions.ConnectionError:
        return "❌ **Backend not available.** Please ensure the backend server is running on http://localhost:8000"
    
    except requests.exceptions.Timeout:
        return "⏱️ **Request timed out.** The backend is taking too long to respond."
    
    except requests.exceptions.RequestException as e:
        return f"❌ **Network error:** {str(e)}"
    
    except json.JSONDecodeError:
        return "❌ **Invalid response format** from backend."
    
    except Exception as e:
        return f"❌ **Unexpected error:** {str(e)}"


def process_user_input(message: str, chat_history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str, str, str]:
    """
    Process user input and update the chat interface.
    
    Args:
        message: User input message
        chat_history: Current chat history
        
    Returns:
        Tuple of (updated_chat_history, empty_input, cart_display, orders_display)
    """
    if not message.strip():
        return chat_history, "", format_cart_display(current_cart), format_past_orders(DUMMY_PAST_ORDERS)
    
    # Get response from backend
    agent_response = send_message_to_backend(message)
    
    # Update chat history
    chat_history.append((message, agent_response))
    
    # For demo purposes, simulate adding items to cart based on keywords
    # In a real implementation, the backend would handle cart logic
    food_keywords = ["pizza", "burger", "sushi", "pasta", "salad", "sandwich", "soup"]
    for keyword in food_keywords:
        if keyword.lower() in message.lower():
            item_name = keyword.capitalize()
            if item_name not in current_cart:
                current_cart.append(item_name)
                break
    
    return (
        chat_history,
        "",  # Clear input field
        format_cart_display(current_cart),
        format_past_orders(DUMMY_PAST_ORDERS)
    )


def place_order() -> Tuple[str, str]:
    """
    Simulate placing an order and clear the cart.
    
    Returns:
        Tuple of (success_message, updated_cart_display)
    """
    global current_cart
    
    if not current_cart:
        return "⚠️ Your cart is empty! Add some items first.", format_cart_display(current_cart)
    
    # Simulate order placement
    order_id = f"ORD-{len(DUMMY_PAST_ORDERS) + 1:03d}"
    items = current_cart.copy()
    
    # Clear cart
    current_cart = []
    
    # In a real app, you would send this to your backend
    success_message = f"✅ **Order placed successfully!**\n\nOrder ID: {order_id}\nItems: {', '.join(items)}\n\nYou'll receive a confirmation email shortly."
    
    return success_message, format_cart_display(current_cart)


def clear_cart() -> str:
    """Clear all items from the cart."""
    global current_cart
    current_cart = []
    return format_cart_display(current_cart)


def create_interface() -> gr.Blocks:
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(title="Food Ordering Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🍕 Food Ordering & Tracking Agent")
        gr.Markdown("Chat with our AI agent to order food, track orders, and manage your cart!")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Chat interface
                chatbot = gr.Chatbot(
                    label="Chat with Food Agent",
                    height=400,
                    placeholder="Start chatting with the food ordering agent..."
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here... (e.g., 'I want to order a pizza')",
                        scale=4
                    )
                    
                    # Voice input
                    voice_input = gr.Audio(
                        label="Voice Message",
                        sources=["microphone"],
                        type="numpy",
                        scale=1
                    )
                
                with gr.Row():
                    send_btn = gr.Button("Send Message", variant="primary")
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
            
            with gr.Column(scale=1):
                # Cart and order info
                cart_display = gr.Markdown(
                    format_cart_display(current_cart),
                    label="Current Cart"
                )
                
                with gr.Row():
                    place_order_btn = gr.Button("🛒 Place Order", variant="primary")
                    clear_cart_btn = gr.Button("🗑️ Clear Cart", variant="secondary")
                
                order_status = gr.Markdown("", label="Order Status")
                
                past_orders = gr.Markdown(
                    format_past_orders(DUMMY_PAST_ORDERS),
                    label="Past Orders"
                )
        
        # Event handlers
        def handle_send(message, history):
            return process_user_input(message, history)
        
        def handle_voice(audio, history):
            # For now, just show that voice was received
            # In a real app, you'd use speech-to-text here
            if audio is not None:
                voice_message = "🎤 Voice message received (speech-to-text not implemented)"
                return process_user_input(voice_message, history)
            return history, "", format_cart_display(current_cart), format_past_orders(DUMMY_PAST_ORDERS)
        
        def handle_place_order():
            return place_order()
        
        def handle_clear_cart():
            return clear_cart(), ""
        
        def handle_clear_chat():
            return [], ""
        
        # Connect event handlers
        send_btn.click(
            handle_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input, cart_display, past_orders]
        )
        
        msg_input.submit(
            handle_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input, cart_display, past_orders]
        )
        
        voice_input.change(
            handle_voice,
            inputs=[voice_input, chatbot],
            outputs=[chatbot, msg_input, cart_display, past_orders]
        )
        
        place_order_btn.click(
            handle_place_order,
            outputs=[order_status, cart_display]
        )
        
        clear_cart_btn.click(
            handle_clear_cart,
            outputs=[cart_display, order_status]
        )
        
        clear_btn.click(
            handle_clear_chat,
            outputs=[chatbot, order_status]
        )
    
    return interface


def main():
    """Main function to launch the Gradio interface."""
    print("🚀 Starting Food Ordering Agent UI...")
    print("📡 Backend expected at:", BACKEND_URL)
    print("💡 Make sure your backend server is running!")
    
    # Create and launch interface
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,       # Default Gradio port
        share=False,            # Set to True for public sharing
        debug=True              # Enable debug mode
    )


if __name__ == "__main__":
    main()
