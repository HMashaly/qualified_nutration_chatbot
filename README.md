# 🥗 qualified_nutration_chatbot — AI Nutrition Coach

A domain-focused chatbot built with LangChain, RAG, and Streamlit for Sprint 2.

## Features

### Core (Phase 1)
- **RAG pipeline** — ChromaDB knowledge base covering healthy eating, weight loss, vegan/vegetarian, halal, allergies, meal planning
- **5 tools**: BMI calculator, TDEE/calorie calculator, macro breakdown, dietary compatibility checker, RAG knowledge search
- **Personalised agent** — user profile (weight, height, goal, diet type) fed into system prompt

### Easy Optional (Phase 2) ✅
- Conversation history export (JSON download)
- Source citations shown for every RAG response
- Tool call visualisation (expandable per message)
- Interactive help guide with example questions

### Medium Optional (Phase 3) ✅
- Multi-model support (gpt-4o-mini / gpt-4o toggle in sidebar)
- Session token usage + cost estimation display

## Setup

### 1. Clone and install
```bash
cd qualified_nutration_chatbot
pip install -r requirements.txt
```

### 2. Start local PostgreSQL
If you use Homebrew on macOS:
```bash
brew install postgresql@16
brew services start postgresql@16
```

Create the database and app user:
```bash
psql postgres
```

```sql
CREATE DATABASE qualified_nutration_chatbot;
CREATE USER qualified_nutration_chatbot_app WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE qualified_nutration_chatbot TO qualified_nutration_chatbot_app;
```

Apply the schema:
```bash
psql -d qualified_nutration_chatbot -f sql/schema.sql
```

### 3. Set your environment variables
Create a `.env` file:
```
OPENAI_API_KEY=sk-...
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=qualified_nutration_chatbot
POSTGRES_USER=qualified_nutration_chatbot_app
POSTGRES_PASSWORD=change_me
```

### 4. Build the knowledge base (run ONCE)
```bash
python rag/ingest.py
```
This embeds the markdown knowledge base into ChromaDB. Only needed once, or when you add/change documents.

### 5. Run the app
```bash
streamlit run app.py
```

### 6. Create the first admin
1. Register a normal account in the app.
2. Promote it manually in PostgreSQL:

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'your_admin_email@example.com';
```

## Project Structure
```
qualified_nutration_chatbot/
├── app.py                    # Streamlit UI
├── auth.py                   # Registration, login, roles, admin helpers
├── db.py                     # PostgreSQL connection and schema init
├── functions/
│   └── agent.py              # LangChain agent wiring
├── rag/
│   ├── ingest.py             # Embed docs → ChromaDB (run once)
├── documents/
│   └── ChromaDB/
│       └── retriever.py      # RAG tool for the agent
├── sql/
│   └── schema.sql            # PostgreSQL schema
├── tools/
│   └── nutrition_tools.py    # BMI, calories, macros, allergen checker
├── knowledgebase/            # Knowledge base (markdown files)
│   ├── healthy_eating_basics.md
│   ├── weight_loss_principles.md
│   ├── vegan_vegetarian_guide.md
│   ├── halal_guide.md
│   ├── allergies_guide.md
│   └── meal_planning.md
├── chroma_db/                # Auto-created after ingest
├── .env                      # Your API key (git-ignored)
├── requirements.txt
└── README.md
```

## Auth Features

- Email + password login backed by PostgreSQL
- Role-based access with `user` and `admin`
- Admin-only dashboard placeholder for login audit and future chatbot logs
- Login attempt audit table for later monitoring and reporting

## Knowledge Base Topics
| File | Covers |
|------|--------|
| `healthy_eating_basics.md` | Macros, micros, food groups, hydration |
| `weight_loss_principles.md` | Caloric deficit, TDEE, Mifflin-St Jeor, body composition |
| `vegan_vegetarian_guide.md` | B12, iron, calcium, omega-3, protein sources, sample meals |
| `halal_guide.md` | Permitted/forbidden foods, hidden haram ingredients, certification |
| `allergies_guide.md` | 14 major allergens, coeliac, lactose intolerance, cross-contamination |
| `meal_planning.md` | Portions, macro splits by goal, batch cooking, label reading |

## Tools

| Tool | What it does |
|------|-------------|
| `search_nutrition_knowledge` | RAG search over knowledge base |
| `calculate_bmi` | BMI + WHO category |
| `calculate_daily_calories` | TDEE via Mifflin-St Jeor + goal adjustment |
| `calculate_macros` | Protein/carb/fat grams from daily calories + goal |
| `check_dietary_compatibility` | Checks food vs vegan/halal/gluten-free/nut-free/dairy-free rules |

## Example Questions to Test
- "What are the best vegan protein sources?"
- "Calculate my BMI — I'm 75kg and 178cm"
- "Is soy sauce halal and gluten-free?"
- "How many calories should I eat? I'm 65kg, 160cm, 30yo female, moderate activity, weight loss"
- "Give me macro targets for 1800 calories and muscle gain"
- "What vitamins do vegans need to supplement?"
- "I'm allergic to nuts and dairy — what are good snack ideas?"
