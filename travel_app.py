import os
import streamlit as st
import google.generativeai as genai
from phi.assistant import Assistant
from phi.tools.duckduckgo import DuckDuckGo

# Configure Gemini API
os.environ["GEMINI_API_KEY"] = "AIzaSyAE1UNYk-qqRezzLnSAwDYgTpKVOvYyW_4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name="gemini-pro",
)


# Create Travel Assistant
travel_assistant = Assistant(
    name="Travel Planner", 
    model=model,
    tools=[DuckDuckGo()],
    instructions=[
        "You are a travel planning assistant. Help users plan their trips by:",
        "1. Researching destinations and providing up-to-date information",
        "2. Finding popular attractions and activities", 
        "3. Suggesting accommodations based on preferences",
        "4. Providing local transportation options",
        "5. Giving budget estimates and travel tips",
        "Always verify information is current before making recommendations"
    ],
    show_tool_calls=True
)

# Set page config and styling
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stTitle {
        color: #1e3d59;
        font-size: 3rem !important;
        text-align: center;
        padding: 2rem 0;
    }
    .stButton>button {
        background-color: #17b890;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header with image
st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1000", use_column_width=True)

# Title and description
st.title("✈️ AI Travel Planner")
st.markdown("""
    <p style='text-align: center; font-size: 1.2rem; color: #666;'>
        Let us help you create unforgettable travel memories! 
        Enter your destination below and let our AI craft the perfect itinerary for you.
    </p>
""", unsafe_allow_html=True)

# Create two columns for inputs
col1, col2 = st.columns(2)

with col1:
    destination = st.text_input("🌎 Where would you like to go?", placeholder="Enter destination...")
    
with col2:
    duration = st.number_input("📅 How many days are you planning to stay?", min_value=1, value=3)

# Additional preferences
st.markdown("### 🎯 Travel Preferences")
cols = st.columns(3)
with cols[0]:
    budget = st.selectbox("Budget Level", ["Budget", "Moderate", "Luxury"])
with cols[1]:
    travel_style = st.selectbox("Travel Style", ["Adventure", "Relaxation", "Cultural", "Family"])
with cols[2]:
    interests = st.multiselect("Interests", ["Food", "History", "Nature", "Shopping", "Art"])

if st.button("✨ Generate Travel Plan"):
    if destination:
        prompt = f"""
        Create a detailed travel plan for {destination} for {duration} days.
        Travel Style: {travel_style}
        Budget Level: {budget}
        Interests: {', '.join(interests) if interests else 'All'}
        
        Please include:
        - Best time to visit and current weather
        - Curated attractions and activities based on interests
        - {budget} level accommodation recommendations
        - Local transportation options and tips
        - Daily budget breakdown
        - Local customs and travel tips
        """
        with st.spinner("🌍 Creating your perfect travel plan..."):
            response = model.generate_content(prompt)
            
            # Display response in a nice format
            st.markdown("## 🎉 Your Personalized Travel Plan")
            st.markdown("""---""")
            st.markdown(response.text)
            
            # Add download button for the plan
            st.download_button(
                label="📥 Download Travel Plan",
                data=response.text,
                file_name=f"travel_plan_{destination}.txt",
                mime="text/plain"
            )
    else:
        st.error("🚫 Please enter a destination to generate your travel plan!")
