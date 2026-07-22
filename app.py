import os
import requests
import asyncio
import streamlit as st
import edge_tts

# Streamlit UI configuration
st.set_page_config(page_title="AI Audio Storyteller", page_icon="📖", layout="centered")

# --- Custom Premium CSS Styling (Glassmorphism UI) ---
def apply_custom_ui(background_url):
    st.markdown(f"""
    <style>
    /* Dynamic full-screen background */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.45)), 
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

    .stSlider{{
        margin-bottom:10px;
    }}

    .stSlider [role="slider"]{{
        background:#00E5FF !important;
        border:3px solid white !important;
        box-shadow:0 0 18px cyan;
    }}

    .stSlider [data-baseweb="slider"] > div:nth-child(2){{
        height:10px;
        border-radius:20px;
        background:linear-gradient(90deg,#00E5FF,#0066FF);
    }}

    .stSlider label{{
        color:white !important;
        font-weight:bold;
        text-align:center;
    }}

    h3{{
        color:white;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize app session state defaults
if "bg_url" not in st.session_state:
    st.session_state.bg_url = "https://images.unsplash.com/photo-1519681393784-d120267933ba"

# Execute application UI design shell
apply_custom_ui(st.session_state.bg_url)

# App UI Header
st.title("📖 Audio Storyteller By Aafreen")
st.write("Enter an idea, and watch the SLM weave a tale narrated by a lifelike neural voice with matching ambiance!")

# User input prompt
user_prompt = st.text_input("Enter a theme or idea:", "A brave drone exploring a hidden valley")

st.markdown("---")
st.subheader("🎚 Story Genre Mixer")

genre_weights = {}

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    genre_weights["Fantasy"] = st.slider("🧙 Fantasy", 0, 100, 80)
with col2:
    genre_weights["Adventure"] = st.slider("🗺 Adventure", 0, 100, 70)
with col3:
    genre_weights["Mystery"] = st.slider("🕵 Mystery", 0, 100, 30)
with col4:
    genre_weights["Sci-Fi"] = st.slider("🚀 Sci-Fi", 0, 100, 50)
with col5:
    genre_weights["Comedy"] = st.slider("😂 Comedy", 0, 100, 20)

col6, col7, col8, col9, col10 = st.columns(5)

with col6:
    genre_weights["Romance"] = st.slider("❤️ Romance", 0, 100, 10)
with col7:
    genre_weights["Horror"] = st.slider("👻 Horror", 0, 100, 5)
with col8:
    genre_weights["Magic"] = st.slider("✨ Magic", 0, 100, 90)
with col9:
    genre_weights["Medieval"] = st.slider("🏰 Medieval", 0, 100, 40)
with col10:
    genre_weights["Cyberpunk"] = st.slider("🤖 Cyberpunk", 0, 100, 25)

# Stable serverless routing endpoints
API_URL = "https://router.huggingface.co/v1/chat/completions"

# Safely fetch token from Streamlit secrets (or fallback cleanly if not set yet)
HF_TOKEN = st.secrets.get("hf_token", "")

# Language Selection
language = st.radio(
    "🌐 Choose Story Language:",
    ["English", "Hindi"],
    horizontal=True
)

if language == "Hindi":
    NEURAL_VOICE = "hi-IN-SwaraNeural"  # Natural and expressive Hindi neural voice
else:
    NEURAL_VOICE = "en-US-BrianNeural"

genre_mix = ""

for genre, value in genre_weights.items():
    if value > 0:
        genre_mix += f"{genre}: {value}%\n"

def generate_story_and_mood(prompt):
    if not HF_TOKEN:
        return "⚠️ Error: Please configure your Hugging Face token in Streamlit secrets.", "default"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    if language == "Hindi":
        language_instruction = (
            "Write the story completely in modern, natural, conversational Hindi "
            "(बोलचाल की हिंदी) as spoken by everyday people today. Avoid overly formal, "
            "archaic, or Sanskritized vocabulary. Make it sound warm and expressive."
        )
    else:
        language_instruction = "Write the story completely in English language." 

    creative_instruction = f"""
       Write an amazing children's story.

      {language_instruction}

      Theme:
      {prompt}

      Genre Equalizer:

      {genre_mix}

      Instructions:
       - Blend every selected genre naturally according to its percentage.
       - Higher percentage means stronger influence.
       - Do NOT mention percentages.
       - Write exactly 4 detailed paragraphs.
       - Include dialogues using natural conversational flow.
       - Include emotions and vivid descriptions.
       - End with a memorable conclusion.
         """
    
    payload_story = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": creative_instruction}],
        "max_tokens": 800,
        "temperature": 0.8
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload_story, timeout=20)
        if response.status_code == 200:
            story_text = response.json()["choices"][0]["message"]["content"].strip()
            
            mood_instruction = f"""
              Based on this story, provide exactly one single English keyword
              representing the setting/environment.

             Examples:
             jungle, space, ocean, castle, desert

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
            return f"Error connecting to SLM model: {response.status_code} - {response.text}", "default"
    except Exception as e:
        return f"Network request failed: {str(e)}", "default"

# Helper function to handle async neural speech generation
async def convert_text_to_neural_audio(text, output_path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# Execution button
if st.button("Generate & Narrate Story"):
    if user_prompt.strip() == "":
        st.warning("Please provide a prompt first!")
    else:
        with st.spinner("The SLM is weaving a magical tale and feeling the mood..."):
            story_text, mood = generate_story_and_mood(user_prompt)
        
        if not story_text.startswith("⚠️") and not story_text.startswith("Error") and not story_text.startswith("Network"):
            st.session_state.bg_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1600&h=900&q=80&sig={mood}"
            apply_custom_ui(st.session_state.bg_url)
            
        st.markdown(f'<div class="story-card"><h3>📜 The Story</h3><p>{story_text.replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)
        
        if not story_text.startswith("⚠️") and not story_text.startswith("Error") and not story_text.startswith("Network"):
            with st.spinner("Synthesizing human-like audio narration..."):
                try:
                    audio_path = "story_narration.mp3"
                    asyncio.run(convert_text_to_neural_audio(story_text, audio_path, NEURAL_VOICE))
                    st.audio(audio_path, format="audio/mp3")
                except Exception as e:
                    st.error(f"Audio generation failed: {e}")

