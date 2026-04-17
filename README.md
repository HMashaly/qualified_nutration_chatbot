# 🥗 qualified_nutration_chatbot

🌐 Live App: https://nutrationchatbot.streamlit.app

AI-powered nutrition assistant using Streamlit + LangChain Agent + RAG (ChromaDB) + OpenAI + PostgreSQL.

---

# 📌 Overview

This project is an AI Nutrition Coach that provides:

* Personalized diet and nutrition guidance
* Calorie, BMI, and macro calculations
* Dietary restriction validation (halal, vegan, gluten-free, etc.)
* Retrieval-Augmented Generation (RAG) over a nutrition knowledge base
* Authentication system with role-based admin dashboard
* Chat history and session tracking and json export for the current session's chat

---

# 🧱 System Architecture

## 🔄 High-Level Flow

```mermaid
flowchart TD

A[User opens Streamlit App] --> B[Authentication Layer]
B -->|Login/Register| C[Session State Initialized]

C --> D[Sidebar Profile Input]
D --> E[Chat Interface]

E --> F[User Question]

F --> G[AgentExecutor]

G --> H[LLM Decision Step]

H -->|choose tool| I[RAG / Calculation / Diet Tool]
H -->|no tool needed| J[Direct Answer]

I --> K[Tool Output]
K --> H

H --> G

G --> L[Final Answer]

L --> M[Streamlit UI Render]
M --> N[Chat History Stored in Session State]
N --> O[PostgreSQL Audit Logs]
```
---

# ⚙️ Key Features

## 🧠 AI & RAG System
- LangChain tool-augmented agent
- GPT-4o / GPT-4o-mini support
- ChromaDB vector search (RAG)
- Automatic knowledge retrieval from embedded nutrition docs

## 🔢 Built-in Nutrition Tools
- BMI calculator
- Daily calorie (TDEE) estimator
- Macro nutrient calculator
- Dietary compatibility checker (vegan, halal, gluten-free, etc.)

## 🔐 Authentication System
- Email/password signup & login
- bcrypt password hashing
- PostgreSQL user storage
- Login audit logging

## 🚦 Rate Limiting
- Max 5 failed login attempts
- Window: 5 minutes
- Automatic cooldown enforcement on repeated failures

## 💬 Chat System
- Multi-turn conversation memory (session-based)
- Tool usage tracking per message
- Source citations for RAG responses

## 📤 JSON Export
- Export full session data including:
  - chat history
  - timestamps
  - model used
  - dietary profile
  - session metadata

## 💰 Cost Tracking
- Token estimation per message
- Approximate cost calculation displayed in sidebar

## 🧾 Admin Panel
- Total users
- Admin users count
- Login audit logs (PostgreSQL)
- Reserved analytics section

## 🧠 Session State Management
- Stored locally in Streamlit:
  - chat history
  - authentication state
  - profile inputs
  - selected model
  - cost + token tracking

## 🗄️ Database Layer
- PostgreSQL backend
- Stores users + login audit logs
- Configurable via env or Streamlit secrets

## 📚 Vector Database (ChromaDB)
- Persistent embeddings storage
- Auto-ingestion on first run
- Supports semantic search over nutrition knowledgebase

---

# 🚀 Execution Summary

1. User logs in
2. Session state initialized
3. User sets dietary profile
4. User asks question
5. AgentExecutor sends query to LLM
6. LLM selects tool OR answers directly
7. Tools execute (RAG / calculations / diet checks)
8. LLM synthesizes final response
9. Streamlit renders output
10. Session + logs updated
---

# ⚙️ Core Components

## 1. 🎯 Streamlit Frontend (`app.py`)

Handles:

* Authentication UI
* Sidebar profile (weight, height, goals, diet)
* Chat interface
* Session state management
* Admin dashboard view

Key responsibilities:

* Sends user input + dietary profile to agent
* Displays response + tool usage + sources

---

## 2. 🤖 LangChain Agent (`agent.py`)

Core reasoning engine.

### Tools used:

* `search_nutrition_knowledge` (RAG via ChromaDB)
* `calculate_bmi`
* `calculate_daily_calories`
* `calculate_macros`
* `check_dietary_compatibility`

### Flow:

User Input → Prompt Template → Tool Selection → LLM → Final Answer

---

## 3. 📚 RAG System (`rag/ingest.py`, `retriever.py`)

### Pipeline:

1. Load markdown files from `knowledgebase/`
2. Split into chunks
3. Generate embeddings (OpenAI `text-embedding-3-small`)
4. Store in ChromaDB
5. Query via similarity search during runtime

---

## 4. 🔐 Authentication (`auth.py`)

Features:

* Email normalization
* Password hashing (bcrypt via passlib)
* Login audit logging
* Rate limiting (5 attempts / 5 min window)

Database tables:

* `users`
* `login_audit`

---

## 5. 🗄 Database Layer (`db.py`)

Supports:

* PostgreSQL (primary)
* Streamlit secrets fallback
* Environment variables fallback

Used for:

* Users
* Login audit logs

---

## 6. 🧠 Tools Layer (`nutrition_tool.py`)

### Available tools:

* BMI calculation (WHO classification)
* TDEE + calorie target calculation
* Macro breakdown calculator
* Dietary compatibility checker
---

## 🔄 Low-Level Flow

```mermaid
flowchart TD
    A[User opens Streamlit App] --> B[Authentication Layer]

    B -->|Login/Register| C[Streamlit Session State Initialized]

    C --> D[Sidebar Profile Input (diet, goals, stats)]
    D --> E[Chat Interface]

    E --> F[User submits question via chat_input]

    F --> G[LangChain AgentExecutor]

    %% TOOL SELECTION LOOP
    G --> H[Tool Selection by LLM (GPT-4o-mini / GPT-4o)]

    H -->|RAG needed| H1[RAG Tool: search_nutrition_knowledge]
    H -->|Calculation needed| H2[Tools: BMI / Calories / Macros]
    H -->|Diet check needed| H3[Tool: check_dietary_compatibility]

    %% RAG FLOW
    H1 --> I[Vectorstore Query (ChromaDB)]
    I --> J[Embeddings similarity search]
    J --> K[Top-k Documents retrieved]

    K --> G

    %% TOOL OUTPUT RETURN
    H2 --> G
    H3 --> G

    %% FINAL GENERATION
    G --> L[LLM final response synthesis]

    L --> M[Streamlit UI rendering]

    M --> N[Session State updates]
    N --> O[Chat history + tokens + cost tracking]

    N --> P[Optional PostgreSQL audit logs]

    %% VECTOR DB BUILD FLOW (OFFLINE / FIRST RUN)
    subgraph OFFLINE_INDEXING[First Run / Build Phase]
        Q[rag/ingest.py] --> R[Load Markdown Knowledgebase]
        R --> S[Chunking (RecursiveTextSplitter)]
        S --> T[Embeddings OpenAI text-embedding-3-small]
        T --> U[ChromaDB Vector Store persisted on disk]
    end
```
---
# 🚀 Run Locally

## 1️⃣ Clone repo
```
git clone https://github.com/HMashaly/qualified_nutration_chatbot
cd qualified_nutration_chatbot
```

## 2️⃣ Create virtual environment
```
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

## 3️⃣ Install dependencies
```
pip install -r requirements.txt
```

If anything is missing, install manually:
```
pip install streamlit langchain langchain-openai langchain-community langchain-chroma chromadb psycopg[binary] python-dotenv passlib[bcrypt] email-validator openai
```

## 4️⃣ Environment variables (.env)

Create a .env file based on env-sample:
```
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## 🧠 First-time setup (RAG)
If running for the first time:
```
python rag/ingest.py
```
This builds the ChromaDB vector store from the knowledgebase.

## ▶️ Run app
```
streamlit run app.py
```

Open:
```
http://localhost:8501
```

## ⚠️ Notes
- If chroma_db/ is missing → auto-created on startup
- .env must include OPENAI_API_KEY (required for LLM + embeddings)
- Agent automatically decides between:
  - RAG (knowledgebase)
  - tools (BMI / calories / macros)
  - direct answer