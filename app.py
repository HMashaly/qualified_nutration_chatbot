"""
qualified_nutration_chatbot — AI Nutrition Coach
Streamlit App: app.py

Run:
    streamlit run app.py
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import re

import streamlit as st

from auth import authenticate_user, create_user, get_admin_dashboard_stats, is_rate_limited
from db import init_database


PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


st.set_page_config(
    page_title="qualified_nutration_chatbot — AI Nutrition Coach",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .nutribot-header {
        background: linear-gradient(135deg, #1a4731 0%, #2d6a4f 50%, #40916c 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .nutribot-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2rem;
        margin: 0;
        color: white;
    }
    .nutribot-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 0.9rem;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px;
    }
    .badge-vegan { background: #dcfce7; color: #166534; }
    .badge-vegetarian { background: #d1fae5; color: #065f46; }
    .badge-halal { background: #fef3c7; color: #92400e; }
    .badge-gluten { background: #fce7f3; color: #9d174d; }
    .badge-nut { background: #ede9fe; color: #5b21b6; }
    .badge-dairy { background: #e0f2fe; color: #075985; }
    .source-pill {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 2px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        color: #475569;
        display: inline-block;
        margin: 2px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def init_session():
    defaults = {
        "messages": [],
        "agent": None,
        "total_tokens": 0,
        "total_cost": 0.0,
        "session_start": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": "gpt-4o-mini",
        "user_id": None,
        "user_email": None,
        "user_role": None,
        "is_authenticated": False,
        "auth_failed_attempts": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat_state():
    st.session_state.messages = []
    st.session_state.agent = None
    st.session_state.total_tokens = 0
    st.session_state.total_cost = 0.0


def logout():
    reset_chat_state()
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.is_authenticated = False
    st.session_state.auth_failed_attempts = []


def build_dietary_profile(profile: dict) -> str:
    parts = []
    if profile["diet_type"]:
        parts.append(f"Diet: {', '.join(profile['diet_type'])}")
    if profile["religious"]:
        parts.append(f"Religious requirements: {', '.join(profile['religious'])}")
    if profile["allergies"]:
        parts.append(f"Allergies/intolerances: {', '.join(profile['allergies'])}")
    parts.append(f"Goal: {profile['goal']}")
    parts.append(
        f"Stats: {profile['weight']}kg, {profile['height']}cm, {profile['age']}yo {profile['gender']}, Activity: {profile['activity']}"
    )
    return " | ".join(parts)


def get_agent(model_name: str):
    import importlib.util

    root = str(Path(__file__).parent.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    agent_path = Path(__file__).parent / "functions" / "agent.py"
    spec = importlib.util.spec_from_file_location("agent_module", agent_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agent_module"] = mod
    spec.loader.exec_module(mod)
    return mod.create_nutribot_agent(model_name=model_name)


def render_header():
    st.markdown("""
    <div class="nutribot-header">
        <h1>🥗 qualified_nutration_chatbot</h1>
        <p>Your AI Nutrition Coach — personalised guidance for healthy eating, weight management, and dietary needs</p>
    </div>
    """, unsafe_allow_html=True)


def render_auth_screen():
    render_header()
    st.info("Sign in to use the chatbot. Admin accounts will also see the audit/logs area.")

    left, right = st.columns([1.2, 1])
    with left:
        tabs = st.tabs(["Sign In", "Register"])

        with tabs[0]:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                limited, retry_after = is_rate_limited(st.session_state.auth_failed_attempts)
                if limited:
                    st.error(f"Too many failed attempts. Try again in about {retry_after} seconds.")
                else:
                    result = authenticate_user(email, password)
                    if result.ok:
                        st.session_state.user_id = result.user["id"]
                        st.session_state.user_email = result.user["email"]
                        st.session_state.user_role = result.user["role"]
                        st.session_state.is_authenticated = True
                        st.session_state.auth_failed_attempts = []
                        st.success(result.message)
                        st.rerun()
                    else:
                        st.session_state.auth_failed_attempts.append(datetime.now(timezone.utc).isoformat())
                        st.error(result.message)

        with tabs[1]:
            with st.form("register_form", clear_on_submit=False):
                new_email = st.text_input("Email", key="register_email")
                new_password = st.text_input("Password", type="password", key="register_password")
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    result = create_user(new_email, new_password)
                    if result.ok:
                        st.success(result.message)
                    else:
                        st.error(result.message)

    with right:
        st.markdown("### Local PostgreSQL Setup")
        st.code(
            "createdb qualified_nutration_chatbot\n"
            "psql -d qualified_nutration_chatbot -f sql/schema.sql",
            language="bash",
        )
        st.markdown(
            "Use a normal registered account first, then promote the first admin with "
            "`UPDATE users SET role = 'admin' WHERE email = 'your_admin_email@example.com';`"
        )


def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown(f"### Signed in as\n`{st.session_state.user_email}`")
        st.caption(f"Role: `{st.session_state.user_role}`")
        if st.button("Log Out", use_container_width=True):
            logout()
            st.rerun()

        st.markdown("---")
        st.markdown("### 👤 Your Profile")

        col1, col2 = st.columns(2)
        with col1:
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.5)
            age = st.number_input("Age", min_value=10, max_value=100, value=30)
        with col2:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
            gender = st.selectbox("Gender", ["Male", "Female"])

        goal = st.selectbox(
            "🎯 Goal",
            ["Weight Loss", "Maintenance", "Muscle Gain", "General Health"],
        )
        activity = st.selectbox(
            "🏃 Activity Level",
            ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
        )

        st.markdown("---")
        st.markdown("### 🥗 Dietary Profile")
        diet_type = st.multiselect(
            "Diet type",
            ["Omnivore", "Vegetarian", "Vegan", "Pescatarian"],
            default=["Omnivore"],
        )
        religious = st.multiselect(
            "Religious / ethical",
            ["Halal", "Kosher", "Hindu Vegetarian"],
        )
        allergies = st.multiselect(
            "Allergies / intolerances",
            ["Gluten-Free", "Dairy-Free", "Nut-Free", "Egg-Free", "Soy-Free", "Shellfish-Free"],
        )

        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        model_choice = st.selectbox(
            "🤖 Model",
            ["gpt-4o-mini", "gpt-4o"],
            index=0 if st.session_state.model == "gpt-4o-mini" else 1,
            help="gpt-4o-mini is faster and cheaper; gpt-4o is more capable",
        )
        if model_choice != st.session_state.model:
            st.session_state.model = model_choice
            st.session_state.agent = None

        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Messages", len(st.session_state.messages))
        with col_b:
            est_cost = round(st.session_state.total_tokens * 0.00000015, 4)
            st.metric("Est. Cost", f"${est_cost}")
        st.caption(f"Session started: {st.session_state.session_start}")

        st.markdown("---")
        export_data = {
            "session_start": st.session_state.session_start,
            "model": st.session_state.model,
            "user_email": st.session_state.user_email,
            "dietary_profile": {
                "diet_type": diet_type,
                "religious": religious,
                "allergies": allergies,
                "goal": goal,
            },
            "messages": [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "timestamp": m.get("timestamp", ""),
                }
                for m in st.session_state.messages
            ],
        }
        st.download_button(
            label="📥 Export Chat (JSON)",
            data=json.dumps(export_data, indent=2),
            file_name=f"qualified_nutration_chatbot_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

        if st.button("🗑️ Clear Chat", use_container_width=True):
            reset_chat_state()
            st.rerun()

    return {
        "weight": weight,
        "age": age,
        "height": height,
        "gender": gender,
        "goal": goal,
        "activity": activity,
        "diet_type": diet_type,
        "religious": religious,
        "allergies": allergies,
    }


def render_active_badges(profile: dict):
    badge_map = {
        "Vegan": "badge-vegan",
        "Vegetarian": "badge-vegetarian",
        "Halal": "badge-halal",
        "Gluten-Free": "badge-gluten",
        "Nut-Free": "badge-nut",
        "Dairy-Free": "badge-dairy",
    }
    active_badges = []
    for item in profile["diet_type"] + profile["religious"] + profile["allergies"]:
        css = badge_map.get(item, "badge-vegan")
        active_badges.append(f'<span class="badge {css}">{item}</span>')

    if active_badges:
        st.markdown(
            f"<div style='margin-bottom:1rem'>Active dietary profile: {''.join(active_badges)}</div>",
            unsafe_allow_html=True,
        )


def render_example_questions():
    """Render example questions as non-clickable suggestions"""
    if st.session_state.messages:
        return
    
    st.markdown("#### 💡 Try asking:")
    
    # Use columns to display examples as non-clickable text
    example_cols = st.columns(3)
    examples = [
        "What are the best vegan protein sources?",
        "Calculate my BMI — I'm 70kg and 175cm",
        "Is soy sauce halal and gluten-free?",
        "How many calories should I eat to lose weight?",
        "What supplements do vegans need?",
        "Give me a gluten-free meal plan for weight loss",
    ]
    
    for i, example in enumerate(examples):
        with example_cols[i % 3]:
            # Display as plain text in a styled container (not clickable)
            st.markdown(f"""
            <div style="
                background-color: #f0f2f6;
                padding: 8px 12px;
                border-radius: 8px;
                margin: 4px 0;
                font-size: 0.85rem;
                color: #1f2937;
                border-left: 3px solid #2d6a4f;
            ">
                💡 {example}
            </div>
            """, unsafe_allow_html=True)


def render_chat_history():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🥗"):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    with st.expander(f"📚 Sources ({len(msg['sources'])} retrieved)", expanded=False):
                        for src in msg["sources"]:
                            st.markdown(f'<span class="source-pill">📄 {src}</span>', unsafe_allow_html=True)
                if msg.get("tools_used"):
                    with st.expander(f"🔧 Tools used ({len(msg['tools_used'])})", expanded=False):
                        for tool in msg["tools_used"]:
                            st.markdown(f"**Tool:** `{tool['tool']}`")
                            st.markdown(f"**Input:** {tool['input']}")
                            st.code(tool["output"], language="text")


def render_help():
    with st.expander("❓ How to use qualified_nutration_chatbot", expanded=False):
        st.markdown("""
        **qualified_nutration_chatbot can help you with:**
        - 🥦 **Nutrition questions** — macros, vitamins, food groups, meal timing
        - ⚖️ **Calculations** — BMI, daily calorie needs, macro splits
        - 🌱 **Vegan/Vegetarian** — protein sources, B12, iron, omega-3, meal ideas
        - 🕌 **Halal** — permissible foods, hidden ingredients, certification
        - 🚫 **Allergies** — the 14 major allergens, cross-contamination, substitutes
        - 📅 **Meal planning** — batch cooking, portions, goal-based plans

        **Example questions:**
        - *"What are good halal protein sources for weight loss?"*
        - *"I'm vegan and lactose intolerant — where do I get calcium?"*
        - *"Calculate my calories: 68kg, 165cm, 28yo female, moderate activity, weight loss"*
        - *"Is gelatin vegan and halal?"*
        - *"Give me a gluten-free vegetarian meal plan"*

        **⚠️ Disclaimer:** qualified_nutration_chatbot provides educational information only. Always consult a registered dietitian or doctor for personalised medical nutrition advice.
        """)


def render_chatbot(profile: dict):
    render_header()
    render_active_badges(profile)
    render_example_questions()
    render_chat_history()

    user_input = st.chat_input("Ask me anything about nutrition, diet, or your health goals...")
    if not user_input:
        render_help()
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    dietary_profile = build_dietary_profile(profile)
    if st.session_state.agent is None:
        with st.spinner("🔄 Loading qualified_nutration_chatbot..."):
            try:
                st.session_state.agent = get_agent(st.session_state.model)
            except Exception as exc:
                st.error(f"❌ Failed to load agent: {exc}")
                st.stop()
    agent = st.session_state.agent

    with st.chat_message("assistant", avatar="🥗"):
        with st.spinner("🌿 Thinking..."):
            try:
                start_time = time.time()
                result = agent.invoke({"input": user_input, "dietary_profile": dietary_profile})
                elapsed = round(time.time() - start_time, 1)

                answer = result.get("output", "Sorry, I couldn't generate a response.")
                intermediate_steps = result.get("intermediate_steps", [])
                tools_used = []
                sources = set()

                for action, observation in intermediate_steps:
                    tool_name = getattr(action, "tool", str(action))
                    tool_input = getattr(action, "tool_input", "")
                    tools_used.append(
                        {
                            "tool": tool_name,
                            "input": str(tool_input),
                            "output": str(observation)[:800],
                        }
                    )
                    if tool_name == "search_nutrition_knowledge":
                        found = re.findall(r"\[Source: ([^\]]+)\]", str(observation))
                        sources.update(found)

                st.session_state.total_tokens += (len(user_input) + len(answer)) // 4
                st.markdown(answer)

                meta_cols = st.columns([3, 1, 1])
                with meta_cols[1]:
                    st.caption(f"⏱️ {elapsed}s")
                with meta_cols[2]:
                    st.caption(f"🤖 {st.session_state.model}")

                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} retrieved)", expanded=False):
                        for src in sources:
                            st.markdown(f'<span class="source-pill">📄 {src}</span>', unsafe_allow_html=True)
                if tools_used:
                    with st.expander(f"🔧 Tools used ({len(tools_used)})", expanded=False):
                        for tool in tools_used:
                            st.markdown(f"**Tool:** `{tool['tool']}`")
                            st.markdown(f"**Input:** {tool['input']}")
                            st.code(tool["output"], language="text")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": list(sources),
                        "tools_used": tools_used,
                        "timestamp": datetime.now().strftime("%H:%M"),
                    }
                )
            except Exception as exc:
                error_msg = f"⚠️ Error: {str(exc)}\n\nPlease try rephrasing your question."
                st.error(error_msg)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M"),
                    }
                )

    render_help()


def render_admin_panel():
    st.markdown("## Admin")
    st.caption("This is the admin-only area. Login audit is live; chatbot logs can be added later.")
    try:
        stats = get_admin_dashboard_stats()
    except Exception as exc:
        st.error(f"Could not load admin dashboard: {exc}")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total users", stats["total_users"])
    with col2:
        st.metric("Admin accounts", stats["total_admins"])

    st.markdown("### Recent login attempts")
    if stats["recent_logins"]:
        st.dataframe(stats["recent_logins"], use_container_width=True)
    else:
        st.info("No login audit entries yet.")

    st.markdown("### Future chatbot logs")
    st.info("Reserved for chat transcript logs, moderation events, and admin analytics.")


init_session()

try:
    init_database()
except Exception as exc:
    render_header()
    st.error(f"Database setup failed: {exc}")
    st.info("Check your PostgreSQL environment variables, ensure the database exists, and restart the app.")
    st.stop()

if not st.session_state.is_authenticated:
    render_auth_screen()
    st.stop()

profile = render_sidebar()
if st.session_state.user_role == "admin":
    chat_tab, admin_tab = st.tabs(["Chatbot", "Admin"])
    with chat_tab:
        render_chatbot(profile)
    with admin_tab:
        render_admin_panel()
else:
    render_chatbot(profile)