
# 🍽️ raise\_hackathon\_prosus\_track

A lightweight, agent-powered food ordering prototype built for the RAISE Hackathon under the Prosus Track. The system integrates a Groq-hosted LLaMA model for intelligent restaurant discovery, menu browsing, and order placement, using a Gradio interface.

---

## 🧱 Requirements

* Python **3.10**
* [Poetry](https://python-poetry.org/docs/#installation)

---

## ⚙️ Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/raise_hackathon_prosus_track.git
   cd raise_hackathon_prosus_track
   ```

2. **Install dependencies using Poetry**

   ```bash
   poetry install
   ```

3. **Set up your environment variables**
   Create a `.env` file in the root directory. Add your API keys:

   ```
   GROQ_API_KEY=your_groq_key_here
   SERP_API_KEY=your_serp_api_key_here
   ```

---

## 📁 Project Structure

```
.
├── app.py               # Main Gradio UI + routing
├── agent.py             # Groq agent setup and function calling
├── tools/
│   ├── restaurant.py    # SERP API integration for discovery
│   ├── menu.py          # Stub menu data (hardcoded)
│   └── order.py         # Cart and checkout logic
├── profile/
│   └── user_graph.py    # Logic for personalizing user experience
├── data/
│   └── sample_menus.json
├── .env                 # Your local environment variables (not committed)
├── requirements.txt     # Optional: fallback dependency list
```

---

## 📝 Notes

* This is a hackathon prototype. APIs are stubbed or mocked where needed.
* You may need to request a SERP API key from [serpapi.com](https://serpapi.com/).

---

Let me know if you'd like:

* A section on contributing or license
* Deployment (e.g., Streamlit/Gradio sharing link or Docker)
* Demo GIF/screenshots or usage examples
