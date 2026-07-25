import os
import requests
import asyncio
import streamlit as st
import edge_tts

# Streamlit UI configuration
st.set_page_config(page_title="AI Science Storyteller", page_icon="🔬", layout="centered")

# --- Custom Premium CSS Styling (Glassmorphism UI) ---
def apply_custom_ui(background_url):
    st.markdown(f"""
    <style>
    /* Dynamic full-screen background */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                    url("{background_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        transition: background 1.0s ease-in-out;
    }}
    
    /* Make header transparent */
    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0);
    }}
    
    /* Elegant container for the story card */
    .story-card {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 25px;
        color: #ffffff;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }}
    
    /* Styling adjustments for headers and paragraph layout text */
    h1, h2, h3, .story-card p, label {{
        color: #ffffff !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* Main body text description color rules */
    [data-testid="stWidgetLabel"] p {{
        color: #ffffff !important;
    }}
    
    /* Force user typed text in inputs to be dark/black for readability */
    .stTextInput>div>div>input {{
        background: rgba(255, 255, 255, 0.85) !important;
        color: #111111 !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        font-weight: 500;
    }}
    
    /* Force Streamlit primary buttons text and styles to stark contrast */
    .stButton>button {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out;
    }}
    
    .stButton>button p {{
        color: #111111 !important;
        font-weight: 600 !important;
    }}
    
    /* Button Hover interaction animation */
    .stButton>button:hover {{
        background-color: #ffffff !important;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(255,255,255,0.3);
    }}

    h3{{
        color:white;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize app session state defaults
if "bg_url" not in st.session_state:
    st.session_state.bg_url = "https://images.unsplash.com/photo-1507413245164-6160d8298b31"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "student_username" not in st.session_state:
    st.session_state.student_username = ""

# Mock database dictionary to register up to 200 students locally in session/memory
# (For a real multi-user public web deployment, connect this to SQLite / Firebase / Supabase)
if "student_db" not in st.session_state:
    st.session_state.student_db = {"student1": "password123"} # Sample default account

apply_custom_ui(st.session_state.bg_url)

# --- STUDENT AUTHENTICATION SYSTEM ---
if not st.session_state.logged_in:
    st.title("🔬 Student Portal Login")
    st.write("Welcome to Professor Phunsuk Wangdu's Science Lab! Please log in or register to enter.")

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register New Student"])

    with auth_tab1:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            if login_user in st.session_state.student_db and st.session_state.student_db[login_user] == login_pass:
                st.session_state.logged_in = True
                st.session_state.student_username = login_user
                st.success(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with auth_tab2:
        reg_user = st.text_input("Choose a Username", key="reg_user")
        reg_pass = st.text_input("Choose a Password", type="password", key="reg_pass")
        if st.button("Register Account"):
            if reg_user.strip() == "" or reg_pass.strip() == "":
                st.warning("Please fill in all fields.")
            elif reg_user in st.session_state.student_db:
                st.warning("Username already exists. Choose another one.")
            else:
                st.session_state.student_db[reg_user] = reg_pass
                st.success("Registration successful! You can now log in from the Login tab.")

# --- MAIN APP INTERFACE (Unlocked after Login) ---
else:
    # Sidebar control for user session management & optional personal token
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.student_username}**")
        
        # Option for user/teacher to input their own API token dynamically per session
        dynamic_hf_token = st.text_input("Hugging Face Token:", type="password", help="Paste your HF token here to run queries.")
        
        st.markdown("---")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.student_username = ""
            st.rerun()

    # App UI Header
    st.title("🔬 Professor Phunsuk Wangdu's Science Stories")
    st.write(f"Hello **{st.session_state.student_username}**! Enter any science concept, and let Professor Phunsuk Wangdu explain it through a fascinating, simple story tailored for school students!")

    # User input prompt
    user_prompt = st.text_input("Enter a science concept (e.g., How do black holes work?, What is photosynthesis?):", "How do plants make food using sunlight?")

    st.markdown("---")

    # Stable serverless routing endpoints
    API_URL = "https://router.huggingface.co/v1/chat/completions"

    # Language Selection
    language = st.radio(
        "🌐 Choose Explanation Language:",
        ["English", "Hindi"],
        horizontal=True
    )

    if language == "Hindi":
        NEURAL_VOICE = "hi-IN-SwaraNeural"  # Expressive Hindi voice
    else:
        NEURAL_VOICE = "en-US-BrianNeural"

    def generate_story_and_mood(prompt, token):
        if not token:
            return "⚠️ Error: Please enter your Hugging Face token in the sidebar to generate stories.", "default"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if language == "Hindi":
            language_instruction = (
                "Write the explanation completely in simple, modern, conversational Hindi "
                "(बोलचाल की हिंदी) suitable for students up to 10th standard, maintaining the inspiring, "
                "curious, and practical teaching style of Phunsuk Wangdu. Avoid heavy technical jargon; "
                "explain scientific terms using creative everyday stories and examples."
            )
        else:
            language_instruction = "Write the explanation completely in simple, creative English using easy-to-understand storytelling suitable for students up to 10th standard, embodying the innovative and joyful teaching spirit of Phunsuk Wangdu." 

        creative_instruction = f"""
            You are Professor Phunsuk Wangdu, an expert, friendly, and innovative specialist science teacher for school students up to 10th grade. 
            Explain the given scientific concept by weaving it into a short, highly engaging, and memorable story.

          {language_instruction}

          Science Concept / Question:
          {prompt}

          Instructions:
           - Teach the core scientific principle clearly through characters or an imaginative adventure, just like Phunsuk Wangdu would (focusing on practical understanding rather than rote learning).
           - Use simple, intuitive analogies that a middle/high school student can effortlessly picture.
           - Write exactly 3 short, easy-to-read paragraphs.
           - Include light dialogues or curious questions to keep the student hooked.
           - Conclude with a quick, fun summary takeaway of the exact science fact.
             """
        
        payload_story = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": creative_instruction}],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload_story, timeout=20)
            if response.status_code == 200:
                story_text = response.json()["choices"][0]["message"]["content"].strip()
                
                mood_instruction = f"""
                  Based on this science story, provide exactly one single English keyword
                  representing the background setting.

                  Examples:
                  laboratory, forest, space, ocean, mountain, garden

                  Do not include punctuation or other words.

                  Story:
                  {story_text}
                 """
                payload_mood = {
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": mood_instruction}],
                    "max_tokens": 10,
                    "temperature": 0.1
                }
                mood_response = requests.post(API_URL, headers=headers, json=payload_mood, timeout=10)
                mood_keyword = "default"
                if mood_response.status_code == 200:
                    mood_keyword = mood_response.json()["choices"][0]["message"]["content"].strip().lower()
                    mood_keyword = mood_keyword.replace(".", "").replace('"', '').replace("'", "").split()[0]
                
                return story_text, mood_keyword
            else:
                return f"Error connecting to AI teacher model: {response.status_code} - {response.text}", "default"
        except Exception as e:
            return f"Network request failed: {str(e)}", "default"

    async def convert_text_to_neural_audio(text, output_path, voice):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    # Execution button
    if st.button("Explain Concept with a Story & Audio"):
        if not dynamic_hf_token.strip():
            st.warning("⚠️ Please provide your Hugging Face token in the sidebar first!")
        elif user_prompt.strip() == "":
            st.warning("Please provide a science concept first!")
        else:
            with st.spinner("Professor Phunsuk Wangdu is preparing a fun science lesson for you..."):
                story_text, mood = generate_story_and_mood(user_prompt, dynamic_hf_token)
            
            if not story_text.startswith("⚠️") and not story_text.startswith("Error") and not story_text.startswith("Network"):
                st.session_state.bg_url = f"https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=1600&h=900&q=80&sig={mood}"
                apply_custom_ui(st.session_state.bg_url)
                
            st.markdown(f'<div class="story-card"><h3>🧪 Professor Phunsuk Wangdu’s Science Story</h3><p>{story_text.replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)
            
            if not story_text.startswith("⚠️") and not story_text.startswith("Error") and not story_text.startswith("Network"):
                with st.spinner("Synthesizing clear teacher narration..."):
                    try:
                        audio_path = f"science_lesson_{st.session_state.student_username}.mp3"
                        asyncio.run(convert_text_to_neural_audio(story_text, audio_path, NEURAL_VOICE))
                        st.audio(audio_path, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Audio generation failed: {e}")