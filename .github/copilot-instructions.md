# qualified_nutration_chatbot — AI Agent Instructions

**Project**: qualified_nutration_chatbot, a domain-focused AI nutrition coach built with LangChain, RAG, and Streamlit.

## Architecture Overview

### Data Flow
1. **Knowledge Base** (`knowledgebase/`) → markdown files on nutrition topics
2. **Ingestion** (`rag/ingest.py`) → splits docs, embeds with OpenAI, stores in ChromaDB
3. **Retrieval** (`documents/ChromaDB/retriever.py`) → LangChain tool that semantic-searches vectorstore
4. **Agent** (`functions/agent.py`) → LangChain AgentExecutor with 5 tools + system rules
5. **UI** (`app.py`) → Streamlit interface that captures user profile (weight, height, age, gender, goals, dietary restrictions) and passes it to agent on every query

### Critical Design Patterns

#### 1. Streamlit Module Isolation (Critical)
- **`app.py`** must call `st.set_page_config()` FIRST—before any other Streamlit calls
- **`functions/agent.py`** MUST NOT import or call streamlit—it's a standalone LangChain module loaded via `importlib`
- **Rule**: Only `app.py` touches Streamlit; all other modules are pure Python/LangChain

#### 2. User Profile Injection
- Sidebar captures: weight, height, age, gender, activity level, goals (weight loss/gain/maintain), dietary restrictions (vegan, vegetarian, halal, kosher, gluten-free, nut-free, dairy-free)
- Profile is **formatted as a system message and passed on every agent invoke**—this ensures sidebar changes apply immediately without re-initializing the agent
- See `agent.py` line 68: `("system", "Saved user profile (obey on this turn):\n{dietary_profile}")`

#### 3. RAG Tool Factory Pattern
- `retriever.py` defines `get_rag_tool(vectorstore)` that returns a LangChain `@tool` function
- This factory binds the vectorstore at creation time and is called in `create_nutribot_agent()`
- Pattern allows the agent to invoke semantic search without tight coupling to ChromaDB

#### 4. Dietary Compliance Rules (System Prompt)
- Agent has strict rules for halal, kosher, vegan, vegetarian
- For ambiguous foods (e.g., "schnitzel"), assumes meat may be pork unless specified halal-certified
- Uses `check_dietary_compatibility` tool to validate specific foods
- See `functions/agent.py` lines 50–65 for the exact rules

## Developer Workflows

### First-Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env with OPENAI_API_KEY
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Build the knowledge base (ONE TIME ONLY)
python rag/ingest.py

# 4. Run the app
streamlit run app.py
```

### Modify Knowledge Base
1. Add/edit `.md` files in `knowledgebase/`
2. Re-run `python rag/ingest.py` to rebuild the vectorstore
3. App will use the new embeddings on next load

### Add a New Tool
1. Define a `@tool` function in `tools/nutrition_tools.py` with docstring (tool name + description)
2. Import it in `functions/agent.py:create_nutribot_agent()`
3. Add to the `tools` list before creating the agent
4. The tool will be available to the agent via LangChain's tool-calling mechanism

### Debug Agent Behavior
- Set `verbose=True` in `AgentExecutor` (line 82 of `functions/agent.py`) to see tool calls and reasoning
- Check `st.session_state.messages` in the UI to inspect stored message history
- Use `app.py` line 140+ (invoke section) to trace how the profile is formatted

## Project-Specific Conventions

### File Organization
- **`app.py`** — Streamlit UI, session state, sidebar, message rendering
- **`functions/agent.py`** — Pure LangChain wiring, no Streamlit, importlib-loaded
- **`rag/ingest.py`** — One-time embedding pipeline; called manually, not by the app
- **`documents/ChromaDB/retriever.py`** — Vectorstore wrapper; defines the RAG tool
- **`tools/nutrition_tools.py`** — Reusable calculation tools (BMI, TDEE, macros, compatibility checker)
- **`knowledgebase/`** — Markdown knowledge base; one file per domain (allergies, halal, vegan, weight loss, meal planning, basics)

### Tool Docstrings
Tools use docstrings as LangChain tool descriptions. They **must** clearly state:
- What the tool does
- Parameters and their units (e.g., "weight_kg", "height_cm")
- Example usage
- When the agent should use it

Example:
```python
@tool
def calculate_bmi(weight_kg: float, height_cm: float) -> str:
    """Calculate Body Mass Index given weight in kg and height in cm. Returns BMI + WHO category."""
```

### Message Structure in `st.session_state.messages`
```python
{
    "role": "user" | "assistant",
    "content": str,
    "sources": [{"source": "file.md", "content": "..."}],  # RAG sources
    "tools_used": [{"name": "calculate_bmi", "input": {...}, "output": "..."}],  # Tool invocations
    "timestamp": "YYYY-MM-DD HH:MM:SS"
}
```

## Key Integration Points

- **OpenAI API**: Called by LangChain's `ChatOpenAI` in `functions/agent.py`; model selected via sidebar toggle (gpt-4o-mini / gpt-4o)
- **ChromaDB**: Initialized by `rag/ingest.py`, persisted to `chroma_db/`, loaded by `rag.ingest.load_vectorstore()` in the agent
- **LangChain Version**: 0.3.25 (see `requirements.txt`); uses tool-calling agent (modern approach, not deprecated ReAct)
- **Streamlit Version**: 1.45.0; configured for wide layout with expanded sidebar

## Common Pitfalls

1. **Importing Streamlit in non-UI modules** → Causes `set_page_config()` multiple-call error. Keep Streamlit imports only in `app.py`.
2. **Forgetting to run `python rag/ingest.py`** → App will fail with "vectorstore not found". This step is mandatory after first clone or knowledge base changes.
3. **Hardcoding paths** → Use `Path(__file__).parent.resolve()` for platform-agnostic paths (see `functions/agent.py` and `rag/ingest.py`).
4. **Modifying `sys.path` after imports** → Add to `sys.path` at the very top of files to ensure `agent`, `rag`, `tools` are importable (see `app.py` lines 7–9).
5. **Assuming profile data on first load** → Sidebar values are defaults (70kg, 170cm, 30yo, Male); always validate in tools.

## Testing & Validation

**Manual Test Queries**:
- "What are the best vegan protein sources?" → Tests RAG + dietary rules
- "Calculate my BMI — I'm 75kg and 178cm" → Tests tool invocation
- "Is soy sauce halal?" → Tests dietary compatibility checker
- Change sidebar profile → re-ask same question → profile should apply immediately

**Environment Check**:
```bash
python -c "import langchain; import streamlit; import chromadb; print('✅ All imports OK')"
```

---

*Last updated: April 2026 | For questions, check `README.md` or review `functions/agent.py` system rules.*
