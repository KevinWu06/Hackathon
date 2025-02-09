import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from PIL import Image

# Configure page with professional settings
st.set_page_config(
    page_title="AI Travel Planner Pro",
    page_icon=Image.open("website_icon"),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@aitravelplanner.com', 
        'Report a bug': 'mailto:bugs@aitravelplanner.com',
        'About': 'AI Travel Planner Pro - Your intelligent travel planning solution'
    }
)

# Enhanced professional styling with modern design elements
st.markdown("""
    <style>
    /* Base styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .main {
        padding: 3rem;
        max-width: 1400px;
        margin: 0 auto;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 3.5em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        background: linear-gradient(135deg, #1976D2, #2196F3);
        color: white;
        border: none;
        box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.3);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding: 2.5rem 1.5rem;
        background: linear-gradient(180deg, #ffffff, #f0f2f6);
        border-right: 1px solid #e0e4e8;
    }
    
    /* Progress bar */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #1976D2, #2196F3);
        border-radius: 100px;
    }
    
    /* Typography */
    h1 {
        color: #1565C0;
        font-weight: 700;
        margin-bottom: 2rem;
        font-size: 2.5rem;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #1976D2;
        font-weight: 600;
        margin: 2rem 0 1.25rem;
        font-size: 1.75rem;
    }
    
    /* Card components */
    .tip-box {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.75rem;
        border-radius: 12px;
        margin: 1.75rem 0;
        border-left: 5px solid #2196F3;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    .plot-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        margin: 2rem 0;
        border: 1px solid #e0e4e8;
    }
    
    .metric-container {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        transition: transform 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
    }
    
    /* Data display */
    .stDataFrame {
        border: 1px solid #e0e4e8;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Chat interface */
    .chat-message {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .chat-message.user {
        background: linear-gradient(145deg, #f0f2f6, #e8eaf0);
        border-left: 4px solid #1976D2;
    }
    
    .chat-message.assistant {
        background: linear-gradient(145deg, #e3f2fd, #bbdefb);
        border-left: 4px solid #2196F3;
    }
    
    .chat-message .content {
        display: flex;
        padding: 0.75rem;
        line-height: 1.6;
    }
    
    /* LeBron Navigator */
    .floating-lebron-nav {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 64px;
        height: 64px;
        z-index: 9999;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .floating-lebron-nav:hover {
        transform: scale(1.15) rotate(5deg);
    }
    
    .floating-lebron-nav img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
        border: 4px solid #1976D2;
        transition: border-color 0.3s ease;
    }
    
    .floating-lebron-nav:hover img {
        border-color: #2196F3;
    }
    
    .lebron-tooltip {
        position: absolute;
        bottom: 76px;
        right: 0;
        background: linear-gradient(135deg, #1976D2, #2196F3);
        color: white;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        white-space: nowrap;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
    }
    
    .floating-lebron-nav:hover .lebron-tooltip {
        opacity: 1;
        transform: translateY(0);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for persistent data
if 'travel_history' not in st.session_state:
    st.session_state.travel_history = []

# Configure Gemini API with secure key handling
os.environ["GEMINI_API_KEY"] = "AIzaSyAE1UNYk-qqRezzLnSAwDYgTpKVOvYyW_4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Optimize model configuration for high-quality responses
generation_config = {
    "temperature": 0.85,
    "top_p": 0.92,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config
)

def calculate_budget_estimate(duration: int, daily_budget: int, destination: str, num_travelers: int) -> dict:
    """
    Calculate detailed budget estimates with standard travel expense ratios.
    """
    total_estimate = daily_budget * duration * num_travelers
    per_person_daily = {
        "accommodation": round(daily_budget * 0.4, 2),  # 40% for accommodation
        "food": round(daily_budget * 0.2, 2),           # 20% for food
        "activities": round(daily_budget * 0.2, 2),     # 20% for activities
        "transportation": round(daily_budget * 0.2, 2)    # 20% for transportation
    }
    
    total_breakdown = {
        "accommodation": per_person_daily["accommodation"] * num_travelers,
        "food": per_person_daily["food"] * num_travelers,
        "activities": per_person_daily["activities"] * num_travelers,
        "transportation": per_person_daily["transportation"] * num_travelers
    }
    
    return {
        "daily_total": daily_budget * num_travelers,
        "total_estimate": total_estimate,
        "per_person_daily": per_person_daily,
        "total_breakdown": total_breakdown
    }

# Helper function to generate each section using a smaller prompt
def generate_section(header: str, prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return f"# {header}\n{response.text}\n"
    except Exception as e:
        return f"# {header}\nError generating this section: {str(e)}\n"

def generate_travel_plan(starting_location: str, destinations: list, start_date: datetime, end_date: datetime, budget: str, interests: list, return_city: str, num_travelers: int) -> str:
    """
    Generate a comprehensive travel plan by breaking the prompt into smaller sections.
    """
    duration = (end_date - start_date).days + 1
    destinations_str = " to ".join(destinations)
    
    # Calculate budget data
    budget_data = calculate_budget_estimate(duration, budget, destinations_str, num_travelers)
    
    # Define smaller prompts for each section
    overview_prompt = (
        f"Write an engaging introduction for a travel plan for {num_travelers} {'person' if num_travelers == 1 else 'people'} "
        f"that starts at {starting_location} and visits {destinations_str} "
        f"before returning to {return_city}. Include travel dates from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} "
        f"({duration} days) and highlight the total daily budget of ${budget_data['daily_total']} (${budget} per person). Use descriptive language, metaphors, and engaging imagery. Do not use more than 7 sentences. Make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."
    )
    
    weather_prompt = (
        f"Describe the typical weather and best time to visit for the destinations {destinations_str} "
        f"during the period from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}. Provide vivid and enticing descriptions. Do not write more than 2 sentences for each destination. Make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."
    )
    
    departure_prompt = (
        f"Provide detailed departure instructions for {num_travelers} {'person' if num_travelers == 1 else 'people'} from {starting_location}. Include tips for getting to the airport/station, "
        f"and estimated costs (including airplane tickets to the first destination in {destinations_str}). Make sure to put dollar signs in front of all monetary values. Do not make this more than 5 bullet points. Add emojis to make it more engaging. Make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."
    )
    
    itinerary_prompt = (
        f"""Generate a day-by-day multi-city itinerary for {num_travelers} {'person' if num_travelers == 1 else 'people'} from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}, going between all of the destinations in {destinations_str} during this time."
        Make sure that each day from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} is included with a plan in the itinerary. DO NOT SKIP ANY DAYS. For each day, include sections for **Morning**, **Afternoon**, and **Evening** with activity descriptions, costs, restaurant recommendations, 
        travel details, hotel accommodation details (with cost), and a daily spending summary. Do not use more than 4 bullet points for each day and NO SUB-BULLETS.
        Make sure to put dollar signs in front of all monetary values.
        Use emojis as bullet points to make it more engaging. Make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."""
    )
    


    return_prompt = (
        f"Outline the return journey to {return_city} from the final destination for {num_travelers} {'person' if num_travelers == 1 else 'people'}. Include transportation options, recommended departure times, "
        "check-in and security tips, and a cost breakdown (including airplane tickets). Make sure to put dollar signs in front of all monetary values. Do not make this more than 5 bullet points. Make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."
    )
    
    accommodations_prompt = (
        f"List and describe recommended accommodations suitable for {num_travelers} {'person' if num_travelers == 1 else 'people'} in {destinations_str}. Include unique selling points, standout features, "
        "atmosphere descriptions, and cost details per night. Make sure to put dollar signs in front of all monetary values. Do not make this more than 5 bullet points. Make sure that there are not italicized blobs of words with no spaces in between. Double check to make sure that the font is consistent."
    )
    
    cuisine_prompt = (
        f"Describe must-try local cuisine for the destinations {destinations_str}. Include details on signature dishes, cultural context, and price ranges for {num_travelers} {'person' if num_travelers == 1 else 'people'}. Keep it to 3 bullet points per unique location. Double check to make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent."
    )
    
    costs_prompt = f"""
    💰 Here's a detailed cost breakdown for your {duration}-day trip for {num_travelers} {'person' if num_travelers == 1 else 'people'}:

    🏷️ Daily Budget Per Person: ${budget}
    🏷️ Total Daily Budget: ${budget_data['daily_total']}
    📊 Total Trip Estimate: ${budget_data['total_estimate']}

    📅 Daily Breakdown Per Person:
    - 🏨 Accommodation: ${budget_data['per_person_daily']['accommodation']} per day
    - 🍽️ Food & Dining: ${budget_data['per_person_daily']['food']} per day
    - 🎯 Activities & Entertainment: ${budget_data['per_person_daily']['activities']} per day
    - 🚌 Local Transportation: ${budget_data['per_person_daily']['transportation']} per day

    📅 Total Daily Group Costs:
    - 🏨 Accommodation: ${budget_data['total_breakdown']['accommodation']} per day
    - 🍽️ Food & Dining: ${budget_data['total_breakdown']['food']} per day
    - 🎯 Activities & Entertainment: ${budget_data['total_breakdown']['activities']} per day
    - 🚌 Local Transportation: ${budget_data['total_breakdown']['transportation']} per day

    💵 Total Trip Cost Categories (Group):
    - 🏢 Total Accommodation: ${budget_data['total_breakdown']['accommodation'] * duration}
    - 🍳 Total Food & Dining: ${budget_data['total_breakdown']['food'] * duration}
    - 🎪 Total Activities: ${budget_data['total_breakdown']['activities'] * duration}
    - 🚕 Total Transportation: ${budget_data['total_breakdown']['transportation'] * duration}

    💡 Please provide a detailed analysis of these costs and suggestions for potential savings when traveling as a group of {num_travelers}. And include the emojis used in this prompt in the response. Double check to make sure that there are not italicized blobs of words with no spaces in between. Make sure that the font is consistent.
    """
    
    # Generate each section using the helper function
    travel_plan = ""
    travel_plan += generate_section("✨ Overview", overview_prompt)
    travel_plan += generate_section("🌤️ Weather and Best Time to Visit", weather_prompt)
    travel_plan += generate_section(f"🚗 Departure from {starting_location}", departure_prompt)
    travel_plan += generate_section("📅 Multi-City Itinerary", itinerary_prompt)
    travel_plan += generate_section(f"🚗 Return to {return_city}", return_prompt)
    travel_plan += generate_section("🏨 Accommodation Recommendations", accommodations_prompt)
    travel_plan += generate_section("🍜 Must-Try Local Cuisine", cuisine_prompt)
    travel_plan += generate_section("💰 Estimated Costs", costs_prompt)
    
    return travel_plan

def get_travel_assistant_response(question: str) -> str:
    """Get AI response in LeBron's style"""
    prompt = f"""
    You are LeBron James acting as a knowledgeable and friendly travel advisor. 
    Respond to this travel-related question in LeBron's voice - casual, confident, and using some of his common phrases.
    Keep responses brief but helpful, and maintain LeBron's personality traits:
    - Use "young fella" or "young king/queen" occasionally
    - Reference basketball metaphors when relevant
    - Stay positive and motivational
    - Use phrases like "you know what I'm saying" or "that's what I'm talking about"
    - Keep it professional but casual
    - Use basketball analogies when giving travel advice
    - Occasionally mention your experience traveling for games
    - Add some of your signature phrases like "Strive for Greatness" or "The Kid from Akron"
    - Be encouraging and mentor-like
    
    Question: {question}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Hey young fella, having some technical difficulties. Let's take a timeout and try again in a bit! 👑"

# Professional sidebar interface with enhanced styling
with st.sidebar:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f8f9fa, #e9ecef); 
             padding: 1.5rem; 
             border-radius: 10px; 
             box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        <h2 style='color: #1976D2; margin-bottom: 1.5rem;'>Trip Parameters</h2>
    """, unsafe_allow_html=True)
    
    # Enhanced traveler input with icon
    st.markdown("👥 **Group Size**")
    num_travelers = st.number_input(
        "Number of Travelers",
        min_value=1,
        max_value=10,
        value=1,
        help="Enter the number of people traveling",
        key="travelers_input"
    )
    
    # Location inputs with map icons
    st.markdown("📍 **Locations**")
    starting_location = st.text_input(
        "Starting Location",
        placeholder="e.g., New York, USA",
        help="Enter your departure city and country",
        key="start_location"
    )
    
    return_city = st.text_input(
        "Return City",
        placeholder="e.g., Los Angeles, USA",
        help="Enter the city you want to return to",
        key="return_location"
    )
    
    # Destination selector with dynamic validation
    st.markdown("🌎 **Destinations**")
    num_destinations = st.number_input(
        "Number of Destinations",
        min_value=1,
        max_value=5,
        value=1,
        help="Select number of destinations (max 5)",
        key="num_dest"
    )
    
    destinations = []
    for i in range(num_destinations):
        dest = st.text_input(
            f"Destination {i+1}",
            placeholder=f"e.g., {'Paris, France' if i==0 else 'Rome, Italy' if i==1 else 'Barcelona, Spain'}",
            key=f"dest_{i}",
            help=f"Enter destination {i+1} city and country"
        )
        if dest:
            destinations.append(dest)
    
    # Date selection with calendar styling
    st.markdown("📅 **Travel Dates**")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            min_value=datetime.today(),
            help="Select your trip start date",
            key="start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            min_value=start_date,
            help="Select your trip end date",
            key="end_date"
        )
    
    # Budget section with enhanced visualization
    st.markdown("💰 **Budget Planning**")
    budget = st.slider(
        "Daily Budget Per Person (USD)",
        min_value=50,
        max_value=2000,
        value=500,
        step=50,
        format="$%d",
        help="Set your daily budget per person in USD",
        key="budget_slider"
    )
    
    # Dynamic budget calculation with styling
    total_budget = budget * num_travelers
    st.markdown(f"""
        <div style='background: #e3f2fd; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
            <p style='margin: 0; color: #1976D2; font-weight: 500;'>
                Total Daily Budget: ${total_budget:,}
                <br><small style='color: #64b5f6;'>
                    (${budget:,} × {num_travelers} {'person' if num_travelers == 1 else 'people'})
                </small>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Enhanced interests selection with categories
    st.markdown("🎯 **Travel Interests**")
    interest_categories = {
        "Cultural": ["Culture & History", "Art & Museums", "Religious Sites", "Local Experiences"],
        "Activities": ["Adventure Sports", "Winter Sports", "Water Sports", "Hiking & Trekking"],
        "Leisure": ["Food & Cuisine", "Shopping", "Nightlife", "Wellness & Spa"],
        "Nature": ["Nature & Outdoors", "Wildlife & Safaris", "Beach Activities", "Eco Tourism"],
        "Special": ["Photography", "Architecture", "Music & Festivals", "Urban Exploration"],
        "Experience": ["Luxury Experiences", "Budget Travel", "Family Activities", "Educational Tours"]
    }
    
    selected_interests = []
    for category, interests_list in interest_categories.items():
        st.markdown(f"**{category}**")
        selected = st.multiselect(
            "",
            interests_list,
            default=[],
            key=f"interests_{category}",
            help=f"Select your {category.lower()} interests"
        )
        selected_interests.extend(selected)
    
    # Custom interest input
    custom_interest = st.text_input(
        "Custom Interest (Optional)",
        placeholder="Enter any specific interest not listed above",
        help="Add your own custom interest"
    )
    if custom_interest:
        selected_interests.append(custom_interest)
    
    interests = selected_interests
    
    # Language preference with flags
    st.markdown("🌐 **Language Preference**")
    language_options = {
        "English": "🇺🇸", "Spanish": "🇪🇸", "French": "🇫🇷",
        "German": "🇩🇪", "Japanese": "🇯🇵", "Chinese": "🇨🇳"
    }
    language = st.selectbox(
        "Preferred Language",
        options=list(language_options.keys()),
        format_func=lambda x: f"{language_options[x]} {x}",
        help="Select your preferred language for the travel plan"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

# Enhanced PDF generation
def create_pdf(travel_plan: str, destination: str) -> bytes:
    """
    Create professionally formatted PDF travel plans with proper markdown handling.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Travel Plan - {destination}")
    
    # Enhanced styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.HexColor('#1976D2')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2196F3')
    )
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        leftIndent=20,
        textColor=colors.HexColor('#424242')
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leftIndent=20
    )
    
    def remove_emojis(text):
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "✨🌤️📅🌅☀️🌙🍽️🚆🏨💰🚌🎭🍜🛡️🎒→✈️🌎📍⭐💡🔍"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub('', text).strip()
    
    def format_markdown(text):
        # Handle bold text by replacing ** with HTML bold tags
        parts = text.split('**')
        formatted_text = ''
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Odd indices are bold
                formatted_text += f'<b>{part}</b>'
            else:
                formatted_text += part
        return formatted_text
    
    content = []
    
    # Add title
    content.append(Paragraph(f"Travel Plan - {destination}", title_style))
    
    # Process the travel plan
    sections = travel_plan.split('#')
    for section in sections[1:]:
        lines = section.split('\n')
        if not lines:
            continue
        current_section = remove_emojis(lines[0].strip())
        content.append(Paragraph(format_markdown(current_section), heading_style))
        bullet_group = []
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            cleaned_line = remove_emojis(line)
            # Handle bullet points
            if line.startswith('-'):
                cleaned_line = cleaned_line[1:].strip()  # Remove the bullet point
                formatted_line = format_markdown(cleaned_line)
                bullet_group.append(f"• {formatted_line}")
            else:
                if bullet_group:  # Add any accumulated bullet points
                    content.append(Paragraph('<br/>'.join(bullet_group), body_style))
                    bullet_group = []
                formatted_line = format_markdown(cleaned_line)
                content.append(Paragraph(formatted_line, body_style))
        # Add any remaining bullet points
        if bullet_group:
            content.append(Paragraph('<br/>'.join(bullet_group), body_style))
        content.append(Spacer(1, 12))
    
    # Build the PDF
    doc.build(content)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# Main content area with professional layout
st.title("🌎 AI Trip Saver Pro")
st.markdown("""
    <div style='background: linear-gradient(135deg, #f6f8fa, #e9ecef); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h3 style='margin:0; color: #1976D2;'>Your Intelligent AI-Powered Travel Planning Solution</h3>
        <p style='margin-top:0.5rem; color: #555;'>Create personalized travel itineraries with advanced AI assistance</p>
    </div>
""", unsafe_allow_html=True)

# Create organized tabs with custom styling
tab_style = """
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #f8f9fa;
            padding: 0.5rem;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #ffffff;
            border-radius: 6px;
            color: #1976D2;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e3f2fd;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1976D2 !important;
            color: white !important;
        }
    </style>
"""
st.markdown(tab_style, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "✈️ Plan Generator", 
    "📊 Budget Analysis", 
    "🏀 LeBron's Travel Assistant"
])

# Initialize tab selection in session state
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = 0

with tab1:
    if st.button("Generate Travel Plan", type="primary", help="Click to create your personalized travel itinerary"):
        if starting_location and destinations and len(destinations) == num_destinations and interests and return_city:
            # Calculate budget estimates
            duration = (end_date - start_date).days + 1
            budget_data = calculate_budget_estimate(duration, budget, " to ".join(destinations), num_travelers)
            
            # Generate and display travel plan with enhanced progress indicator
            with st.spinner('🌟 Crafting your personalized travel plan...'):
                travel_plan = generate_travel_plan(starting_location, destinations, start_date, end_date, budget, interests, return_city, num_travelers)
                
                # Save to history with success message
                st.session_state.travel_history.append({
                    "starting_location": starting_location,
                    "destination": " to ".join(destinations),
                    "return_city": return_city,
                    "date": start_date.strftime("%Y-%m-%d"),
                    "duration": duration,
                    "num_travelers": num_travelers,
                    "budget_per_person": budget,
                    "total_budget": budget * num_travelers,
                    "estimated_cost": budget_data["total_estimate"]
                })
                st.success("✅ Travel plan generated successfully!")
            
            # Store travel plan in session state
            st.session_state.current_travel_plan = travel_plan
            
            # Display the plan with enhanced styling
            st.markdown("""
                <div style='background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
            """, unsafe_allow_html=True)
            st.markdown(travel_plan)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Enhanced download options with modern styling
            st.markdown("<br>", unsafe_allow_html=True)
            download_container = st.container()
            with download_container:
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download as Text",
                        data=travel_plan,
                        file_name=f"travel_plan_{'-'.join(destinations).replace(' ', '_')}.txt",
                        mime="text/plain",
                        help="Download your travel plan in text format"
                    )
                with col2:
                    try:
                        pdf_data = create_pdf(travel_plan, " to ".join(destinations))
                        st.download_button(
                            label="📥 Download as PDF",
                            data=pdf_data,
                            file_name=f"travel_plan_{'-'.join(destinations).replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            help="Download your travel plan as a professionally formatted PDF"
                        )
                    except Exception as e:
                        st.error(f"⚠️ Error creating PDF: {str(e)}")
        else:
            st.error("⚠️ Please complete all required fields to generate your travel plan.")

    # Add floating LeBron navigator with enhanced styling
    st.markdown("""
        <div class="floating-lebron-nav" onclick="document.getElementsByClassName('st-emotion-cache-1v7p1xi e1nzilvr5')[2].click();">
            <div class="lebron-tooltip">Chat with LeBron - Your Personal Travel Advisor</div>
            <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png" alt="Chat with LeBron">
        </div>
    """, unsafe_allow_html=True)

with tab2:
    if len(st.session_state.travel_history) > 0:
        df = pd.DataFrame(st.session_state.travel_history)
        
        # Enhanced budget visualization with modern styling
        st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        st.subheader("💰 Trip Cost Comparison")
        fig = px.bar(
            df, 
            x="destination", 
            y="estimated_cost", 
            color="total_budget", 
            title="Estimated Costs by Destination",
            template="streamlit",
            labels={
                "destination": "Destination",
                "estimated_cost": "Estimated Cost ($)",
                "budget": "Daily Budget"
            }
        )
        
        fig.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(
            fig, 
            use_container_width=True, 
            theme="streamlit",
            config={'displayModeBar': True}
        )
        
        # Enhanced trip duration analysis
        st.subheader("📊 Trip Duration Analysis")
        fig2 = px.scatter(
            df, 
            x="date", 
            y="duration",
            size="estimated_cost",
            color="destination",
            title="Trip Duration vs Date",
            template="streamlit",
            labels={
                "date": "Travel Date",
                "duration": "Duration (Days)",
                "estimated_cost": "Total Estimated Cost ($)",
                "destination": "Destination"
            }
        )
        
        fig2.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            hovermode='closest',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(
            fig2, 
            use_container_width=True, 
            theme="streamlit",
            key="duration_plot",
            on_select="rerun",
            selection_mode=["box", "lasso"]
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Professional summary statistics with enhanced styling
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        st.subheader("📈 Summary Statistics")
        stats_cols = st.columns(4)
        
        with stats_cols[0]:
            st.metric(
                "Total Trips", 
                len(df),
                delta=None,
                help="Total number of trips planned"
            )
        
        with stats_cols[1]:
            st.metric(
                "Average Duration", 
                f"{df['duration'].mean():.1f} days",
                delta=f"{df['duration'].std():.1f} days σ",
                help="Average trip duration (with standard deviation)"
            )
        
        with stats_cols[2]:
            st.metric(
                "Average Total Cost", 
                f"${df['estimated_cost'].mean():,.2f}",
                delta=f"${df['estimated_cost'].std():,.2f} σ",
                help="Average total trip cost (with standard deviation)"
            )
        
        with stats_cols[3]:
            most_visited = df['destination'].mode().iloc[0]
            st.metric(
                "Most Popular Destination",
                most_visited,
                help="Most frequently planned destination"
            )
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced interactive table with modern styling
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        st.subheader("📋 Detailed Trip History")
        st.dataframe(
            df.style.format({
                'estimated_cost': '${:,.2f}',
                'duration': '{} days'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn(
                    "Travel Date",
                    format="MMM DD, YYYY",
                ),
                "estimated_cost": st.column_config.NumberColumn(
                    "Total Estimated Cost",
                    format="$%.2f",
                ),
                "duration": st.column_config.NumberColumn(
                    "Duration",
                    format="%d days",
                ),
                "budget": st.column_config.NumberColumn(
                    "Daily Budget",
                    format="$%d/day",
                ),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        st.info("💡 Generate travel plans to view detailed budget analysis.")

with tab3:
    st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.image("https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png", width=60)
    with col2:
        st.subheader("🏀 Chat with LeBron")
    
    st.markdown("Hey young fella! I'm LeBron, and I'm here to help you plan your next adventure. What's on your mind? 👑")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history with enhanced styling
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Update the chat input placeholder with modern styling
    if prompt := st.chat_input("Ask King James about your travel plans..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            response = get_travel_assistant_response(prompt)
            st.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Add clear chat button with enhanced styling
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History", help="Remove all chat messages"):
            st.session_state.chat_history = []
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Enhanced footer with professional tips and modern styling
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        <h3>💡 Professional Travel Tips</h3>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li>🔍 Research destination-specific entry requirements and travel regulations</li>
            <li>🏨 Consider booking accommodations in advance for better rates</li>
            <li>🌍 Monitor travel advisories and local health guidelines</li>
            <li>🛡️ Invest in comprehensive travel insurance for international trips</li>
        </ul>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);'>
        <h3>🔍 Support & Resources</h3>
        <ul style='list-style-type: none; padding-left: 0;'>
            <li>📧 Contributor: https://github.com/KevinWu06</li>
            <li>📚 Contributor: https://github.com/briankim06</li>
            <li>👥 Contributor: https://github.com/Bevid11</li>
        </ul>
        </div>
    """, unsafe_allow_html=True)
