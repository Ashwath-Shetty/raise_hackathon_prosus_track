# 🍽️ FoodBot — AI-powered Food Ordering Assistant - Raise Hackathon - Prosus Track

[![Live Demo](https://img.shields.io/badge/🔊%20Live%20Demo-HuggingFace-blue?style=for-the-badge)](https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot)

> **Try it live**: [https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot](https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot)

---

## ✨ Overview

**FoodBot** is an intelligent, interactive chatbot that helps users order food effortlessly. It takes a user's location and food preference, searches for the best nearby restaurants using **SerpAPI**, and responds with restaurant suggestions using **LLM-powered tools**.

This project is designed using **LangChain agents**, orchestrated to provide modular, clean, and explainable AI behavior. It was built as part of a **Raise hackathon & Prosus track**.

---

## 🤖 Features

* 🔍 **Location Normalization** using LLM
* 🌟 **Top Restaurant Search** using Google Maps via SerpAPI
* 🤝 **Agent Orchestration** with LangChain
* 🔄 **In-memory Knowledge Graph** to remember users
* 🎨 **Gradio UI** for fast prototyping and deployment
* ⚡ **Groq API** + **LLaMA 3** for fast, low-latency inference

---

---

### 📁 Project Structure

```
raise_hackathon_prosus_track/
│
├── app.py                         # Entry point to launch the Gradio interface
├── agent.py                       # Defines the main FoodOrderingAgent using LangChain
├── prompts.py                     # Contains prompt templates and API keys
├── tools.py                       # Custom LangChain Tools (location normalization, restaurant search, etc.)
├── utils.py                       # Utility functions (normalization, rendering graphs, etc.)
├── models.py                      # Data models using @dataclass (Restaurant, MenuItem, etc.)
│
├── assets/
│   └── image.webp                 # (Optional) Architecture or agent flow image for README
│
├── notebooks/                     # Jupyter notebooks for experiments (cleaned before push)
│
├── requirements.txt               # Package list for pip-based installation
├── pyproject.toml                 # Poetry configuration
├── README.md                      # Project documentation (you're reading it!)
```

---


## 📊 Architecture

### Agent Design

The core agent is a `FoodOrderingAgent` built with LangChain's ReAct paradigm and powered by:

* **LLM (Groq + LLaMA3)**: For location understanding, reasoning
* **Tools:**

  * `LocationNormalizerTool`
  * `RestaurantSearchTool`
  * `MenuTool` 


### Modular Components

* `agent.py` — Orchestration logic
* `tools.py` — LangChain tools (wrappers over SerpAPI, Groq)
* `prompts.py` — API setup and shared clients
* `models.py` — Dataclasses for restaurants, menus, users
* `utils.py` — Support functions and graph renderer
* `app.py` — Gradio chatbot app launcher

---

## 🌐 Live Demo

Launch the chatbot here:
**🔗 [https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot](https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot)**

---

## 🚀 Quickstart

### Option 1: Using Poetry (Recommended)

#### 1. Clone the repository

```bash
git clone https://github.com/your-username/raise_hackathon_prosus_track.git
cd raise_hackathon_prosus_track
```

#### 2. Install with Poetry

```bash
poetry env use python3.10
poetry install
poetry shell
```

#### 3. Setup environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
SERP_API_KEY=your_serp_api_key
```

Or export directly:

```bash
export GROQ_API_KEY=your_groq_api_key
export SERP_API_KEY=your_serp_api_key
```

#### 4. Run the chatbot

```bash
python app.py
```

### Option 2: Using pip

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Set API keys (same as above)

#### 3. Run the app

```bash
python app.py
```

---

## 💼 Requirements

### Poetry (preferred)

```toml
[tool.poetry.dependencies]
python = "3.10"
gradio = "5.35.0"
groq = "0.29.0"
httpx = "0.28.1"
langchain = "0.3.26"
langchain_groq = "0.3.5"
matplotlib = "3.10.3"
networkx = "3.4.2"
Pillow = "11.3.0"
pydantic = "2.11.7"
requests = "2.32.4"
```

### `requirements.txt`

```
gradio==5.35.0
groq==0.29.0
httpx==0.28.1
langchain==0.3.26
langchain_groq==0.3.5
matplotlib==3.10.3
networkx==3.4.2
Pillow==11.3.0
pydantic==2.11.7
requests==2.32.4
```

---

## 🌎 Deploying to Hugging Face Spaces

1. **Add `README.md` metadata** at the top of the file (already done).
2. **Add `.huggingface.yaml`** (optional for advanced settings)
3. **Set secrets**:

   * Go to **Space Settings > Secrets**
   * Add:

     ```
     GROQ_API_KEY=your_groq_api_key
     SERP_API_KEY=your_serp_api_key
     ```
4. **Ensure `requirements.txt` is correct and versions are pinned**
5. **Push to Hugging Face**

```bash
git remote add space https://huggingface.co/spaces/Ashwath-Shetty/food-ordering-bot
git push space main
```

---

## 💰 API Usage Notes

### Groq API (LLM)

* Fast inference with LLaMA3-8B
* Used for natural language prompts like location understanding

### SerpAPI (Google Maps)

* Required for real-time restaurant discovery
* **Free tier gives 100 searches/month - this is a bottle neck & we might exhaust the api limit soon**. if you see chatbot is failing to respond after giving location info, it's probably because we hit the api limit, if you're testing multiple times try to test using the same location & food type - e.x: location - MG road Bengaluru, food - pizza.

---

## 🤝 Sample Conversation

```plaintext
👤: hi
🤖: Hello! Welcome to our food ordering service!  I'm here to help you find and order delicious food. What's your location so I can find restaurants near you?

👤: i'm near jyothi nivas koramangala
🤖: Great! I've set your location to Koramangala, Bengaluru, India. What type of food are you craving today? (e.g., pizza, burgers, sushi, etc.)

👤: pizza
🤖: 🍽️ Top 3 restaurants found for 'pizza' in Koramangala, Bengaluru, India:

    Si Nonna's - The Original Sourdough Pizza - Koramangala, Bengaluru
    📍 Ground Floor, Evantha Praha, No.64, Koramangala, Bengaluru, Karnataka 560034, India
    🍴 pizza
    ⭐⭐⭐⭐ (4.8/5)
    Pizza Hut | Koramangla, Bangalore
    📍 487, 80 Feet Rd, opposite to BATA Shoes, 6th Block, Koramangala, Bengaluru, Karnataka 560095, India
    🍴 pizza
    ⭐⭐⭐⭐ (4.6/5)
    Pasta Street Koramangala
    📍 Ground floor, 751, 80 Feet Rd, 4th Block, Koramangala, Bengaluru, Karnataka 560034, India
    🍴 pizza
    ⭐⭐⭐⭐ (4.4/5)
    Which restaurant would you like to order from? Just tell me the name or number.

👤: pasta street
🤖: Excellent choice! Here's the menu for Pasta Street Koramangala:

🍽️ Menu for Pasta Street Koramangala:

📂 Appetizer
   • Focaccia Frenzy - $6.99
     Freshly baked focaccia served with garlic butter and herbs.

   • Bruschetta Bliss - $8.99
     Toasted baguette topped with diced tomatoes, basil, and mozzarella, drizzled with balsamic glaze.

 📂 Main Course
   • Margherita Pizza - $12.99
     Classic tomato, mozzarella, and basil on sourdough crust.

   • Quattro Formaggi - $14.99
     Four-cheese pizza with mozzarella, parmesan, gorgonzola, and ricotta, served with a side of garlic bread.

   • Meat Lover's Masterpiece - $16.99
     Loaded pizza with pepperoni, sausage, bacon, and ham, topped with mozzarella and served with a side of garlic bread.

👤: add 1 Veggie Delight, 2 Margherita Pizza 
🤖: 🛒 Added to cart:
    - 1 x Veggie Delight
    - 2 x Margherita Pizza

    🛒 Your Cart (Pasta Street Koramangala):
    - 1x Veggie Delight: $15.99
    - 2x Margherita Pizza: $25.98

    💰 Total: $41.97

    Would you like to add more or checkout?

👤: checkout
🤖: Perfect! Here's your order summary:

    🛒 Your Cart (Pasta Street Koramangala):
    - 1x Veggie Delight: $15.99
    - 2x Margherita Pizza: $25.98

    💰 Total: $41.97

    Would you like to confirm this order? (yes/no)

👤: yes
🤖: 🎉 Order confirmed! Your order #ORD20250708034045 has been placed successfully.

    Delivery time: 30-45 minutes
    Restaurant: Pasta Street Koramangala
    Total: $41.97

    Thank you for your order! You'll receive updates via SMS.



```
**click on show knowledge graph to see the knowledge graph** 
![Knowledge graph](assets/image.webp)

---

## 🔍 Troubleshooting

* **`OSError: Cannot find empty port`**

  * Solution: On Hugging Face, don’t use `server_port`. Use `demo.launch(server_name="0.0.0.0")`


* **API key not set**

  * Ensure `.env` exists or variables are exported before running

---

## 💍 Acknowledgments

* [Groq](https://groq.com/) — blazing fast LLM inference
* [LangChain](https://www.langchain.com/) — modular agent orchestration
* [Gradio](https://www.gradio.app/) — quick LLM UIs
* [SerpAPI](https://serpapi.com/) — restaurant and location data

---

## 📖 License

MIT License. See `LICENSE` file.

---

## 🚀 What's Next?

Here are some exciting directions and improvements planned for the project:

* **Integrate Order Confirmation via WhatsApp (Twilio)**
  Add a mock payment flow and integrate Twilio to send WhatsApp messages for order confirmations, making the user experience feel more realistic and complete.

* **Improve Menu Retrieval System**
  This remains the hardest challenge. Neither SerpAPI nor Tavily provide structured menu data. Web scraping for menus is inconsistent and time-consuming—especially difficult to implement reliably within the short span of a 4-day hackathon. Exploring OCR + image menus or structured data from restaurant websites could be future solutions.

* **Smoother Natural Language Conversations**
  Enhance the fluidity and realism of user-bot interactions. This involves refining the prompt structure, memory context, fallback handling, and introducing intent classification to better interpret diverse inputs.

* **Enable True Asynchronous Execution**
  Currently, the app uses synchronous API and LLM calls. Adopting full `async/await` support will improve performance, especially during multi-step reasoning with external API calls and chained agent workflows.

* **Smarter Knowledge Graph with Personalized Context**
  The Knowledge Graph currently tracks user preferences (like cuisine types and favorite restaurants) and location, stored in-memory. In future versions, we plan to:

  * **Persist the graph** to a database or local file for long-term user history.
  * **Use prior visit data** to tailor conversations—e.g., “Would you like to reorder from Chianti Pizza?”
  * **Incorporate context over sessions**, so the bot remembers repeat users or recommends based on past behavior.

  **Current Challenges**:

  * The in-memory implementation resets between sessions (especially on stateless platforms like Hugging Face Spaces).
  * Maintaining a light, queryable, and LLM-friendly representation of graph data without overengineering.
  * Balancing memory vs. personalization without leaking information across users in shared deployments.

---

