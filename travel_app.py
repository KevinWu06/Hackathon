import os
from datetime import datetime, timedelta
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


# Create Travel Assistant for Day-by-Day Planning
travel_assistant = Assistant(
    name="Travel Planner", 
    model=model,
    tools=[DuckDuckGo()],
    instructions=[
        "You are a travel planning assistant. Create detailed day-by-day itineraries by:",
        "1. Starting with arrival day logistics and accommodation check-in",
        "2. Planning each day with morning, afternoon and evening activities",
        "3. Grouping nearby attractions and activities efficiently each day",
        "4. Including transportation between locations for each day",
        "5. Suggesting meal times and recommended local restaurants",
        "6. Providing accommodation options for all budgets (hostels, budget hotels, mid-range, luxury)",
        "7. Accounting for opening hours and time needed at each spot",
        "8. Building in flexibility for weather and preferences",
        "9. Ending with departure day logistics",
        "Provide daily budget estimates for different spending levels (budget, moderate, luxury) and verify all information is current"
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
st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1000", use_container_width=True)

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
    # Date selection
    start_date = st.date_input("📅 Start Date", min_value=datetime.today())
    end_date = st.date_input("📅 End Date", min_value=start_date)
    duration = (end_date - start_date).days + 1

# Additional preferences
st.markdown("### 🎯 Travel Preferences")
cols = st.columns(3)
with cols[0]:
    budget = st.text_input("💰 What's your total budget? (USD)", value="1000")
    try:
        budget = float(budget.replace(',', ''))
    except ValueError:
        st.error("Please enter a valid number for budget")
        budget = 1000
with cols[1]:
    travel_styles = st.multiselect("Travel Styles", ["Adventure", "Relaxation", "Cultural", "Family", "Solo", "Romantic", "Educational"])
with cols[2]:
    interests = st.multiselect("Interests", ["Food & Cuisine", "History & Heritage", "Nature & Outdoors", "Shopping", "Art & Museums", "Music & Entertainment", "Local Experiences", "Photography", "Sports & Activities", "Wellness & Spa"])

if st.button("✨ Generate Travel Plan"):
    if destination:
        prompt = f"""
        Create a detailed travel plan for {destination} from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({duration} days) with a total budget of ${budget:,.2f} USD.
        Travel Styles: {', '.join(travel_styles) if travel_styles else 'Flexible'}
        Interests: {', '.join(interests) if interests else 'All'}
        
        Please include:
        - Best time to visit and current weather for these specific dates
        - Curated attractions and activities based on selected interests and travel styles
        - Accommodation recommendations within the budget (allocate ~40% of total budget)
        - Local transportation options and tips
        - Detailed budget breakdown showing how to best utilize ${budget:,.2f} for:
          * Accommodations
          * Daily meals
          * Activities and attractions
          * Transportation
          * Miscellaneous expenses
        - Local customs and travel tips
        - Money-saving suggestions to maximize the budget
        - Special events or festivals happening during the selected dates
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
                file_name=f"travel_plan_{destination}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    else:
        st.error("🚫 Please enter a destination to generate your travel plan!")
