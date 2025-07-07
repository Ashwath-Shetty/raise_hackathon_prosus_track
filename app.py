import gradio as gr
from agent import FoodOrderingAgent
from utils import render_knowledge_graph
from prompts import GROQ_API_KEY


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
        8. **Click 'Show Knowledge Graph' (at the end when your order is succesfull" ** to visualize your preferences and orders  
        """)
    
    return demo


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