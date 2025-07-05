# raise_hackathon_prosus_track

requirements:
- have python 3.10
- install poetry
- once poetry is installed go to the base working directory & do do poetry install.

proposed repo structure
.
├── app.py               ← main Gradio UI + routing
├── agent.py             ← Groq agent setup + function calling
├── tools/
│   ├── restaurant.py    ← SERP API integration
│   ├── menu.py          ← Hardcoded/stub menu loader
│   └── order.py         ← Cart, checkout, etc.
├── profile/
│   └── user_graph.py    ← User knowledge graph logic
├── data/
│   └── sample_menus.json
├── .env
└── requirements.txt
