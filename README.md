# 🎯 TalentScout – AI-Powered Hiring Assistant

TalentScout is a **professional AI-driven hiring assistant** built with **Streamlit** and the **Google Gemini API**. It guides candidates through an initial screening process, collects their information, generates tailored technical questions, and suggests relevant job roles with companies. Perfect for tech recruitment agencies or teams looking to streamline their interview workflow.

---

## 💡 Features

- **Interactive AI Chatbot**: Engages candidates in a friendly, conversational manner.
- **Automated Screening**:
  - Collects candidate info: Full Name, Email, Phone, Experience, Desired Roles, Location, Tech Stack.
  - Generates 3–5 technical questions per technology (max 10 questions).
  - Suggests relevant job roles and example companies.
- **Sentiment Analysis**: Tracks sentiment for candidate responses (positive, neutral, negative).
- **Downloadable Reports**: Export the candidate transcript and technical evaluation as JSON.
- **Responsive UI**: Clean, modern, and mobile-friendly interface built with Streamlit.

---

## 🛠 Technology Stack

- **Frontend**: Streamlit (Python)
- **AI**: Google Gemini API (`gemini-1.5-flash` model)
- **Data Storage**: Local JSONL files (`data/candidates.jsonl`)
- **Environment Variables**: Managed via `.env`

---

## ⚡ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/talentscout.git
cd talentscout
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
GEMINI_API_KEY=your_gemini_api_key_here
HASH_SALT=your_custom_salt_here
DATA_DIR=data
streamlit run app.py



## File Structure
talentscout/
├── app.py                # Main Streamlit app
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── data/                 # Stores candidate submissions
└── README.md
