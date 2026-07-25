import os
import asyncio
import streamlit as st
import edge_tts
from google import genai

# Streamlit UI configuration
st.set_page_config(page_title="AI Science Storyteller", page_icon="🔬", layout="centered")

# --- Custom Premium CSS Styling & Animations (Glassmorphism UI) ---
def apply_custom_ui(background_url):
    st.markdown(f"""
    <style>
    /* Dynamic full-screen background */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.55)), 
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
    
    /* Elegant animated container for the story card */
    .story-card {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 30px;
        color: #ffffff;
        margin-top: 25px;
        margin-bottom: 25px;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
        animation: fadeInScale 0.8s ease-in-out;
    }}

    @keyframes fadeInScale {{
        0% {{
            opacity: 0;
            transform: translateY(20px) scale(0.98);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
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
    
    /* Force user typed text in inputs to be clear for readability */
    .stTextInput>div>div>input {{
        background: rgba(255, 255, 255, 0.88) !important;
        color: #111111 !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        font-weight: 500;
    }}
    
    /* Force Streamlit primary buttons text and styles to stark contrast */
    .stButton>button {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease-in-out;
    }}
    
    .stButton>button p {{
        color: #111111 !important;
        font-weight: 700 !important;
    }}
    
    /* Button Hover interaction animation */
    .stButton>button:hover {{
        background-color: #ffffff !important;
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(255,255,255,0.4);
    }}

    /* Selectbox custom styling */
    .stSelectbox>div>div>div {{
        background: rgba(255, 255, 255, 0.88) !important;
        color: #111111 !important;
        border-radius: 8px !important;
        font-weight: 600;
    }}

    h3 {{
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize app session state defaults
if "bg_url" not in st.session_state:
    st.session_state.bg_url = "https://images.unsplash.com/photo-1507413245164-6160d8298b31"

apply_custom_ui(st.session_state.bg_url)

# App UI Header
st.title("🔬 Professor Phunsuk Wangdu's Masterclass")
st.write("Enter any science concept, select your academic standard, and let Professor Phunsuk Wangdu break down complex concepts with crystal-clear explanations and immersive stories!")

# Standard Selector for Students (1st to 10th standard)
standard_options = [
    "1st Standard", "2nd Standard", "3rd Standard", "4th Standard", "5th Standard",
    "6th Standard", "7th Standard", "8th Standard", "9th Standard", "10th Standard"
]
selected_standard = st.selectbox("📚 Select Student Standard:", standard_options, index=4)

# User input prompt
user_prompt = st.text_input("Enter a science concept or question (e.g., How do black holes work?, Why do leaves change color?):", "How do plants make food using sunlight?")

st.markdown("---")

# Safely fetch Google API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")

# Pass the key explicitly to avoid authentication misses
client = genai.Client(api_key=GOOGLE_API_KEY)

# Fixed professional neural voice in English
NEURAL_VOICE = "en-US-BrianNeural"

def generate_story_and_mood(prompt, grade_level):
    if not GOOGLE_API_KEY:
        return "⚠️ Backend Error: GOOGLE_API_KEY is missing in the system environment configuration.", "default"
    
    try:
        # Initialize the official Google GenAI client
        client = genai.Client(api_key=GOOGLE_API_KEY)

        creative_instruction = f"""
            You are Professor Phunsuk Wangdu, an elite, world-class specialist science teacher known for making complex science phenomenally clear, intuitive, and engaging.
            Explain the given scientific concept tailored specifically for a student in **{grade_level}**.

          Science Concept / Question:
          {prompt}

          Core Pedagogical Guidelines:
           - Match the cognitive depth, vocabulary level, and comprehension style precisely to **{grade_level}** (Keep it simpler and highly visual for lower primary standards, and introduce accurate scientific terminology with deep conceptual clarity for upper grades like 8th to 10th).
           - Weave the concept into an immersive, crystal-clear story or thought experiment that eliminates confusion completely.
           - Use clean, structured formatting with exactly 3 well-defined paragraphs.
           - Ensure high conceptual clarity so the student grasps the fundamental law, mechanism, or working principle effortlessly.
           - Conclude with a memorable core scientific takeaway summary.
             """
        
        # Generate story content
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=creative_instruction,
        )
        story_text = response.text.strip()
        
        # Generate background keyword mood
        mood_instruction = f"""
          Based on this science explanation, provide exactly one single English keyword
          representing the visual background setting.

          Examples:
          laboratory, forest, space, ocean, mountain, cosmos, microscopic

          Do not include punctuation or other words.

          Story:
          {story_text}
         """
        mood_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=mood_instruction,
        )
        mood_keyword = "default"
        if mood_response.text:
            mood_keyword = mood_response.text.strip().lower()
            mood_keyword = mood_keyword.replace(".", "").replace('"', '').replace("'", "").split()[0]
        
        return story_text, mood_keyword

    except Exception as e:
        return f"Error connecting to Google GenAI model: {str(e)}", "default"

async def convert_text_to_neural_audio(text, output_path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# Execution button
if st.button("✨ Start Masterclass Lesson & Audio"):
    if user_prompt.strip() == "":
        st.warning("Please provide a science concept first!")
    else:
        with st.spinner(f"Professor Phunsuk Wangdu is tailoring a high-clarity lesson for {selected_standard}..."):
            story_text, mood = generate_story_and_mood(user_prompt, selected_standard)
        
        if not story_text.startswith("⚠️") and not story_text.startswith("Error"):
            st.session_state.bg_url = f"https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&w=1600&h=900&q=80&sig={mood}"
            apply_custom_ui(st.session_state.bg_url)
            
        st.markdown(f'<div class="story-card"><h3>🧪 Professor Phunsuk Wangdu’s Masterclass ({selected_standard})</h3><p>{story_text.replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)
        
        if not story_text.startswith("⚠️") and not story_text.startswith("Error"):
            with st.spinner("Synthesizing professional high-definition narration..."):
                try:
                    audio_path = "masterclass_lesson.mp3"
                    asyncio.run(convert_text_to_neural_audio(story_text, audio_path, NEURAL_VOICE))
                    st.audio(audio_path, format="audio/mp3")
                except Exception as e:
                    st.error(f"Audio generation failed: {e}")