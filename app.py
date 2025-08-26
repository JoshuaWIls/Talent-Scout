import os
import re
import json
import time
import hashlib
from typing import Dict, List, Any
from dataclasses import dataclass, field
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HASH_SALT = os.getenv("HASH_SALT", "dev-salt")

if not GEMINI_API_KEY:
    st.error("Invalid Gemini API key.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop", "thanks", "thank you"}

DATA_DIR = os.environ.get("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
CANDIDATES_PATH = os.path.join(DATA_DIR, "candidates.jsonl")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^[+0-9()\-\s]{7,}$")

def sha256_hex(text: str) -> str:
    return hashlib.sha256((HASH_SALT + text).encode("utf-8")).hexdigest()

SYSTEM_PROMPT = """
You are TalentScout, a polite, professional hiring assistant for a tech recruitment agency.
Your tasks:
1. Greet candidates and explain purpose.
2. Collect: Full Name, Email, Phone, Years of Experience, Desired Position(s), Location, Tech Stack.
3. Generate 3–5 questions per technology, capped at 10 total.
4. Suggest 5 relevant job roles and companies that hire for them.
5. Maintain context, handle follow-ups, and never drift off-topic.
6. Exit gracefully when the user types exit/bye/quit/etc.
"""

COMBINED_PROMPT = """
Given the following tech stack: {tech_stack}

1. Generate 3–5 technical interview questions, capped at 10.
2. Suggest 5 relevant job roles.
3. For each role, suggest example companies that typically hire for it.

Return JSON ONLY like this:

{{
  "questions": [
    "Question 1",
    "Question 2"
  ],
  "roles": [
    {{
      "role": "Backend Developer",
      "companies": ["Google", "Amazon", "Netflix"]
    }}
  ]
}}
"""

SENTIMENT_PROMPT = """
Classify sentiment of this message as: "positive", "neutral", or "negative".
Reply with one word only.
Message:
{message}
"""

@dataclass
class Candidate:
    full_name: str = ""
    email_hash: str = ""
    phone_hash: str = ""
    years_experience: str = ""
    desired_positions: str = ""
    current_location: str = ""
    tech_stack: str = ""
    transcript: List[Dict[str, str]] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    roles: List[Dict[str, Any]] = field(default_factory=list)
    sentiment_notes: List[str] = field(default_factory=list)

    def to_record(self) -> Dict[str, Any]:
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "full_name": self.full_name,
            "email_hash": self.email_hash,
            "phone_hash": self.phone_hash,
            "years_experience": self.years_experience,
            "desired_positions": self.desired_positions,
            "current_location": self.current_location,
            "tech_stack": self.tech_stack,
            "questions": self.questions,
            "roles": self.roles,
            "sentiments": self.sentiment_notes,
        }

def make_model():
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT.strip(),
        generation_config={"temperature": 0.4}
    )

def generate_questions_and_roles(model, tech_stack: str):
    prompt = COMBINED_PROMPT.format(tech_stack=tech_stack)
    try:
        resp = model.generate_content(prompt)
        data = json.loads(resp.text)
        return data.get("questions", []), data.get("roles", [])
    except Exception:
        return [f"Explain your experience with {t.strip()}." for t in tech_stack.split(",")][:5], []

def analyze_sentiment(model, message: str) -> str:
    try:
        resp = model.generate_content(SENTIMENT_PROMPT.format(message=message))
        label = resp.text.strip().lower()
        return label if label in {"positive","neutral","negative"} else "neutral"
    except:
        return "neutral"

def is_valid_email(email): return bool(EMAIL_REGEX.match(email.strip()))
def is_valid_phone(phone): return bool(PHONE_REGEX.match(phone.strip()))

def save_candidate(c: Candidate):
    with open(CANDIDATES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(c.to_record()) + "\n")

st.set_page_config(
    page_title="TalentScout Assistant", 
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Global Styles */
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding-bottom: 120px;
    }
    
    /* Header Styles */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 0;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 16px 20px;
        border-radius: 20px 20px 8px 20px;
        margin: 12px 0 12px auto;
        max-width: 75%;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
        font-size: 0.95rem;
        line-height: 1.4;
        word-wrap: break-word;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        color: #2c3e50;
        padding: 16px 20px;
        border-radius: 20px 20px 20px 8px;
        margin: 12px auto 12px 0;
        max-width: 75%;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        font-size: 0.95rem;
        line-height: 1.4;
        word-wrap: break-word;
    }
    
    .message-role {
        font-weight: 600;
        margin-bottom: 4px;
        opacity: 0.8;
        font-size: 0.85rem;
    }
    .welcome-container {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border-radius: 20px;
        border: 1px solid #e9ecef;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    
    .welcome-title {
        font-size: 2rem;
        color: #2c3e50;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .welcome-subtitle {
        font-size: 1.1rem;
        color: #6c757d;
        line-height: 1.6;
        max-width: 600px;
        margin: 0 auto;
    }
    .questions-container {
        background: linear-gradient(135deg, #a3d8a3, #8ccf8c);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 2px solid #28a745;
        box-shadow: 0 8px 32px rgba(40, 167, 69, 0.2);
    }
    
    .questions-header {
        color: #155724;
        text-align: center;
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .questions-subtitle {
        text-align: center;
        color: #155724;
        margin-bottom: 2rem;
        font-size: 1rem;
    }
    
    .question-item {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .question-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .question-number {
        color: #28a745;
        font-weight: 600;
        margin-right: 8px;
    }
    
    /* Fixed Input Container - Updated to remove white background */
    .fixed-input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: transparent !important;
        border-top: none !important;
        padding: 1rem;
        z-index: 1000;
        box-shadow: none !important;
    }
    .input-field {
        flex: 1;
    }
    
    /* Form Controls */
    .stTextInput > div > div > input {
        background: white !important;
        border: 2px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        color: #2c3e50 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1), 0 4px 16px rgba(0,0,0,0.15) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #adb5bd !important;
        font-style: italic;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3) !important;
        min-width: 100px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a67d8, #6b46c1) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Restart Button */
    .restart-container {
        text-align: center;
        margin: 2rem 0;
        padding: 2rem;
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border-radius: 16px;
        border: 1px solid #e9ecef;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #28a745, #20c997) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 16px 32px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        min-width: 250px !important;
        box-shadow: 0 4px 16px rgba(40, 167, 69, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #218838, #1ea085) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(40, 167, 69, 0.4) !important;
    }
    
    /* Success Message */
    .success-container {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #28a745;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 500;
        margin: 2rem 0;
    }
    
    /* Download Button */
    .download-container {
        text-align: center;
        margin: 1.5rem 0;
    }
    
    /* Hide Streamlit elements and remove footer */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        margin-top: -80px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden !important;}
    header {visibility: hidden;}
    
    /* Remove any remaining footer elements */
    .stApp > footer,
    .stApp footer,
    [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    
    /* Ensure body doesn't have extra padding/margin at bottom */
    body {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Remove any white space at the bottom */
    .stApp {
        padding-bottom: 0 !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

if "model" not in st.session_state: st.session_state.model = make_model()
if "candidate" not in st.session_state: st.session_state.candidate = Candidate()
if "stage" not in st.session_state: st.session_state.stage = "greet"
if "chat" not in st.session_state: st.session_state.chat = []
if "latest_json" not in st.session_state: st.session_state.latest_json = {}
if "input_counter" not in st.session_state: st.session_state.input_counter = 0

def add(role, msg):
    st.session_state.chat.append({"role": role, "msg": msg})
    st.session_state.candidate.transcript.append({"role": role, "msg": msg})

def greet():
    add("assistant", "Hello! I'm TalentScout, your professional hiring assistant. I'll help you through our initial screening process by gathering your information and asking tailored technical questions. Let's begin — what's your full name?")

if st.session_state.stage == "greet" and not st.session_state.chat:
    greet()

def handle_input(user_msg):
    c = st.session_state.candidate
    model = st.session_state.model

    if user_msg.lower() in EXIT_KEYWORDS:
        st.session_state.stage = "end"
        return

    sent = analyze_sentiment(model, user_msg)
    c.sentiment_notes.append(sent)

    if st.session_state.stage == "greet":
        c.full_name = user_msg.strip()
        st.session_state.stage = "collect"
        add("assistant", "Thank you! How many years of professional experience do you have?")
        return

    if st.session_state.stage == "collect":
        if not c.years_experience:
            c.years_experience = user_msg.strip()
            add("assistant", "Great! What position(s) are you interested in applying for?")
        elif not c.desired_positions:
            c.desired_positions = user_msg.strip()
            add("assistant", "Perfect! Where are you currently located?")
        elif not c.current_location:
            c.current_location = user_msg.strip()
            add("assistant", "Excellent! Please list your technical skills and tech stack (separated by commas).")
        elif not c.tech_stack:
            c.tech_stack = user_msg.strip()
            add("assistant", "Thank you! What's your email address?")
        elif not c.email_hash:
            if is_valid_email(user_msg):
                c.email_hash = sha256_hex(user_msg.lower())
                add("assistant", "Perfect! Finally, what's your phone number?")
            else:
                add("assistant", "That doesn't appear to be a valid email address. Could you please provide a valid email?")
        elif not c.phone_hash:
            if is_valid_phone(user_msg):
                c.phone_hash = sha256_hex(user_msg)
                st.session_state.stage = "questions"
                qs, roles = generate_questions_and_roles(model, c.tech_stack)
                c.questions = qs
                c.roles = roles
                
                add("assistant", f"Excellent, {c.full_name}! I've prepared some technical questions tailored to your expertise. Please take your time to answer them thoughtfully.")
                
                st.session_state.show_questions = True
                
                if roles:
                    role_msg = "Based on your background, here are some relevant positions and companies that might interest you:\n\n"
                    for role in roles:
                        role_msg += f"• **{role['role']}** — Companies like {', '.join(role['companies'])}\n"
                    add("assistant", role_msg)
                
                st.session_state.latest_json = c.to_record()
                add("assistant", "You can answer the questions one by one or provide comprehensive responses. Type 'exit' when you're finished.")
            else:
                add("assistant", "That phone number doesn't seem to be in a valid format. Please provide a valid phone number.")
    elif st.session_state.stage == "questions":
        add("assistant", "Thank you for your response! Feel free to continue with additional answers or type 'exit' when you're ready to conclude.")

def finalize():
    save_candidate(st.session_state.candidate)
    add("assistant", f"Thank you, {st.session_state.candidate.full_name}! Your application has been successfully submitted. Our team will review your responses and get back to you shortly. We appreciate your time and interest in joining our network!")

# Header
st.markdown("""
<div class="header-container">
    <h1 class="header-title">🎯 TalentScout</h1>
    <p class="header-subtitle">Professional Hiring Assistant powered by Advanced AI</p>
</div>
""", unsafe_allow_html=True)

# Main content container
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Chat messages
if st.session_state.chat:
    for m in st.session_state.chat:
        role = "You" if m["role"] == "user" else "TalentScout"
        if m["role"] == "user":
            st.markdown(f'''
            <div class="user-message">
                <div class="message-role">{role}</div>
                {m["msg"]}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="assistant-message">
                <div class="message-role">{role}</div>
                {m["msg"]}
            </div>
            ''', unsafe_allow_html=True)
else:
    st.markdown('''
    <div class="welcome-container">
        <h2 class="welcome-title">Welcome to TalentScout!</h2>
        <p class="welcome-subtitle">
            I'm here to help you through our professional screening process. 
            I'll gather your information, understand your background, and provide 
            tailored technical questions to showcase your expertise.
        </p>
    </div>
    ''', unsafe_allow_html=True)

# Questions section
if st.session_state.stage == "questions" and hasattr(st.session_state, 'show_questions') and st.session_state.candidate.questions:
    st.markdown("""
    <div class="questions-container">
        <h2 class="questions-header">📋 Technical Interview Questions</h2>
        <p class="questions-subtitle">Please provide detailed responses based on your experience with these technologies:</p>
    </div>
    """, unsafe_allow_html=True)
    
    for i, question in enumerate(st.session_state.candidate.questions):
        st.markdown(f'''
        <div class="question-item">
            <span class="question-number">Question {i+1}:</span>
            {question}
        </div>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input section
if st.session_state.stage != "end":
    st.markdown(f'''
    <div class="fixed-input-container">
    ''', unsafe_allow_html=True)
    
    with st.form(key=f"input_form_{st.session_state.input_counter}", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_msg = st.text_input(
                "Message", 
                placeholder="Type your response here...",
                label_visibility="collapsed",
                key=f"user_input_{st.session_state.input_counter}"
            )
        
        with col2:
            submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and user_msg.strip():
            add("user", user_msg)
            handle_input(user_msg)
            st.session_state.input_counter += 1
            st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Auto-focus script
    st.markdown(f"""
    <script>
    function focusInput() {{
        setTimeout(() => {{
            const input = parent.document.querySelector('input[data-testid*="user_input_{st.session_state.input_counter}"]') ||
                         parent.document.querySelector('.stTextInput input:last-of-type');
            if (input) {{
                input.focus();
                input.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
        }}, 100);
    }}
    
    focusInput();
    setTimeout(focusInput, 200);
    setTimeout(focusInput, 500);
    
    const observer = new MutationObserver(() => setTimeout(focusInput, 50));
    if (parent.document.body) observer.observe(parent.document.body, {{ childList: true, subtree: true }});
    </script>
    """, unsafe_allow_html=True)
else:
    finalize()
    
    st.markdown('''
    <div class="success-container">
        ✅ Conversation completed successfully!
    </div>
    ''', unsafe_allow_html=True)
    
    if st.session_state.latest_json:
        st.markdown('<div class="download-container">', unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Interview Summary",
            data=json.dumps(st.session_state.latest_json, indent=2),
            file_name=f"talentscout_interview_{int(time.time())}.json",
            mime="application/json",
            use_container_width=False
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="restart-container">
        <p style="margin-bottom: 1.5rem; color: #6c757d; font-size: 1.1rem;">
            Ready to conduct another interview?
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Interview", use_container_width=True, type="primary"):
            st.session_state.candidate = Candidate()
            st.session_state.stage = "greet"
            st.session_state.chat = []
            st.session_state.latest_json = {}
            st.session_state.input_counter = 0
            if hasattr(st.session_state, 'show_questions'):
                delattr(st.session_state, 'show_questions')
            st.rerun()