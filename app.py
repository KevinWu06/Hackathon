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
# Add new imports for Google Calendar
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import pickle
from PIL import Image

# Configure page with professional settings
st.set_page_config(
    page_title="AI Travel Planner Pro",
    page_icon="✈️",
    layout="wide", 
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@aitravelplanner.com',
        'Report a bug': 'mailto:bugs@aitravelplanner.com',
        'About': 'AI Travel Planner Pro - Your intelligent travel planning solution'
    }
)

# Enhanced professional styling
st.markdown("""
    <style>
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main {
        padding: 2.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3.2em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .css-1d391kg {
        padding: 2.5rem 1.5rem;
        background-color: #fafafa;
    }
    .stProgress .st-bo {
        background-color: #2196F3;
    }
    .sidebar-content {
        padding: 1.5rem;
        background-color: #f8f9fa;
    }
    h1 {
        color: #1976D2;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    h2 {
        color: #2196F3;
        font-weight: 500;
        margin: 1.5rem 0 1rem;
    }
    .tip-box {
        background-color: #f5f7fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        border-left: 4px solid #2196F3;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .plot-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
    }
    .metric-container {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    /* Chat interface styling */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .chat-message.user {
        background-color: #f0f2f6;
    }
    
    .chat-message.assistant {
        background-color: #e3f2fd;
    }
    
    .chat-message .content {
        display: flex;
        padding: 0.5rem;
    }
    
    /* Floating LeBron Navigator */
    .floating-lebron-nav {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        z-index: 9999;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .floating-lebron-nav:hover {
        transform: scale(1.1);
    }
    
    .floating-lebron-nav img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: 3px solid #1976D2;
    }
    
    .lebron-tooltip {
        position: absolute;
        bottom: 70px;
        right: 0;
        background: #1976D2;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 14px;
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .floating-lebron-nav:hover .lebron-tooltip {
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for persistent data
if 'travel_history' not in st.session_state:
    st.session_state.travel_history = []

# Configure Gemini API with secure key handling
os.environ["GEMINI_API_KEY"] = "AIzaSyAE1UNYk-qqRezzLnSAwDYgTpKVOvYyW_4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service():
    """Get or create Google Calendar API service"""
    creds = None
    
    # Load credentials from pickle file if it exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Error building calendar service: {str(e)}")
        return None

def add_to_google_calendar(travel_plan, start_date, end_date, destinations):
    """Add travel itinerary to Google Calendar"""
    try:
        service = get_google_calendar_service()
        if not service:
            st.error("Could not initialize Google Calendar service")
            return
            
        # Parse the travel plan to create calendar events
        lines = travel_plan.split('\n')
        current_date = start_date
        
        for line in lines:
            if '**Morning**:' in line or '**Afternoon**:' in line or '**Evening**:' in line:
                # Extract time of day and activity
                time_of_day = line.split('**')[1].lower()
                activity = line.split(':', 1)[1].strip()
                
                # Set event times based on time of day
                if 'morning' in time_of_day:
                    start_time = current_date.replace(hour=9, minute=0)
                    end_time = current_date.replace(hour=12, minute=0)
                elif 'afternoon' in time_of_day:
                    start_time = current_date.replace(hour=13, minute=0)
                    end_time = current_date.replace(hour=17, minute=0)
                else:  # evening
                    start_time = current_date.replace(hour=18, minute=0)
                    end_time = current_date.replace(hour=22, minute=0)
                
                # Create calendar event
                event = {
                    'summary': f"Travel: {', '.join(destinations)} - {time_of_day.title()}",
                    'description': activity,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'UTC',
                    },
                }
                
                try:
                    service.events().insert(calendarId='primary', body=event).execute()
                except Exception as e:
                    st.error(f"Error adding event to calendar: {str(e)}")
                    return
            
            # Move to next day if we see a new date marker
            if "# 📅" in line:
                current_date += timedelta(days=1)
        
        st.success("Successfully added travel itinerary to Google Calendar!")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

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

def calculate_budget_estimate(duration: int, daily_budget: int, destination: str) -> dict:
    """
    Calculate detailed budget estimates with standard travel expense ratios.
    """
    total_estimate = daily_budget * duration
    
    breakdown = {
        "accommodation": round(daily_budget * 0.4, 2),  # 40% for accommodation
        "food": round(daily_budget * 0.2, 2),           # 20% for food
        "activities": round(daily_budget * 0.2, 2),     # 20% for activities
        "transportation": round(daily_budget * 0.2, 2)  # 20% for transportation
    }
    
    return {
        "daily_total": daily_budget,
        "total_estimate": total_estimate,
        "breakdown": breakdown
    }

def generate_travel_plan(starting_location: str, destinations: list, start_date: datetime, end_date: datetime, budget: str, interests: list, return_city: str) -> str:
    """
    Generate comprehensive travel plans using AI with structured formatting.
    """
    duration = (end_date - start_date).days + 1
    destinations_str = " to ".join(destinations)
    
    prompt = f"""
    Create a detailed multi-destination travel plan starting from {starting_location} and returning to {return_city} that uses AT LEAST 80% of the daily budget of ${budget} every day. DO NOT USE more than 100% of the ${budget} for any singular day on the itinerary.
    All recommendations for accommodations, activities, food, and transportation MUST be realistic and achievable within this budget. Put every cost in USD. Triple check the following for any formatting errors and correctness in calculations before printing the itinerary. 
    Make sure to print the entire itinerary every single time. Don't just stop halfway through. (Make sure there are no itallicized words with no spaces in between)

    Starting Location: {starting_location}
    Destinations: {destinations_str}
    Return City: {return_city}
    Travel Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({duration} days)
    Daily Budget: ${budget} per day
    Interests: {', '.join(interests)}
    
    Please provide the response in the following structured format, using emojis, bold text (**), italics (_), and bullet points to make the content engaging:

    # ✨ Overview
    [Write an engaging introduction using descriptive language and metaphors about the trip and why these destinations complement each other perfectly]
    
    # 🌤️ Weather and Best Time to Visit
    [Vivid description of the weather and atmosphere during the travel period for each destination]
    
    # 🚗 Departure from {starting_location}
    [Detailed information about departing from the starting location, including:
    - 🏠 **Getting to the Airport/Station**: [transportation options and costs]
    - ⏰ **Recommended Arrival Time**: [timing suggestions]
    - 💳 **Check-in and Security**: [important tips]
    - 💰 **Departure Costs**: [breakdown of costs]]
    (Make sure that this is formatted correctly!)
    (Make sure to include the airplane tickets for the departure city to first location!)
    
    # 📅 Multi-City Itinerary
    [Create an exciting day-by-day breakdown for EACH day from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}, MUST INCLUDE ALL OF THE FOLLOWING AND COSTS(if applicable):
    - 🌅 **Morning**: [activities and costs with descriptive details]
    - ☀️ **Afternoon**: [activities and costs with engaging descriptions]
    - 🌙 **Evening**: [activities and costs with atmospheric details]
    - 🍽️ **Where to Eat**: [restaurant recommendations with signature dishes and MUST INCLUDE COSTS]
    - 🚆 **Travel Details**: [if applicable, with practical tips]
    - 🏨 **Accommodation**: [hotel details with standout features] [MUST INCLUDE COST AND BE PRESENT IN EVERY DAY'S ITINERARY]
    - 💰 **Daily Spending**: $X (separate bullet point)]
    
    # 🚗 Return to {return_city}
    [Detailed information about returning to {return_city}, including:
    - 🏠 **Getting to the Airport/Station**: [transportation options and costs]
    - ⏰ **Recommended Departure Time**: [timing suggestions]
    - 💳 **Check-in and Security**: [important tips]
    - 💰 **Return Costs**: [breakdown of costs including airplane tickets]]
    
    # 🏨 Accommodation Recommendations
    [Curated list of accommodations with unique selling points and atmosphere descriptions]
    
    # 🚌 Transportation
    [Comprehensive transportation guide with insider tips and local knowledge]
    
    # 🎭 Local Customs & Etiquette
    [Engaging cultural insights and etiquette tips written as interesting stories or scenarios]
    
    # 🍜 Must-Try Local Cuisine
    [Mouth-watering descriptions of local dishes with cultural context and price ranges]
    
    # 🛡️ Safety Tips
    [Essential safety information presented in a clear, actionable format]
    
    # 💰 Estimated Costs
    [Detailed breakdown with visual organization using bullets and categories]
    **Total Trip Cost: $X**
    
    # 🎒 Packing Recommendations
    [Smart packing list organized by category with insider tips]

    Re-check for any formatting errors (including when there are itallicized words with no spaces in between) and correctness in calculations before printing the itinerary.
    !!!Make sure to print the entire itinerary every single time. Don't just stop halfway through.!!!
    Make sure that the costs for each day and the total cost of the trip are summed up correctly.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating travel plan: {str(e)}"

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

# Professional sidebar interface
with st.sidebar:
    st.title("Trip Parameters")
    
    # Add starting location input
    starting_location = st.text_input(
        "Starting Location",
        placeholder="e.g., New York, USA",
        help="Enter your departure city and country"
    )
    
    # Add return city input
    return_city = st.text_input(
        "Return City",
        placeholder="e.g., Los Angeles, USA",
        help="Enter the city you want to return to"
    )
    
    # Enhanced destination input
    destinations = []
    num_destinations = st.number_input(
        "Number of Destinations",
        min_value=1,
        max_value=5,
        value=1,
        help="Select number of destinations for your trip"
    )
    
    for i in range(num_destinations):
        dest = st.text_input(
            f"Destination {i+1}",
            placeholder="e.g., Tokyo, Japan",
            key=f"dest_{i}",
            help=f"Enter destination {i+1} name and country"
        )
        if dest:
            destinations.append(dest)
    
    # Improved date selection
    start_date = st.date_input(
        "Start Date",
        min_value=datetime.today(),
        help="Select your trip start date"
    )
    end_date = st.date_input(
        "End Date",
        min_value=start_date,
        help="Select your trip end date"
    )
    
    # Enhanced budget slider
    budget = st.slider(
        "Daily Budget (USD)",
        min_value=0,
        max_value=2000,
        value=500,
        step=50,
        format="$%d",
        help="Set your daily budget in USD"
    )
    
    # Refined interests selection with "Other" option
    predefined_interests = [
        "Culture & History", "Food & Cuisine", "Nature & Outdoors", 
        "Shopping", "Art & Museums", "Nightlife", "Adventure Sports",
        "Local Experiences", "Photography", "Architecture", "Wellness & Spa",
        "Music & Festivals", "Religious Sites", "Wine & Spirits", "Beach Activities",
        "Wildlife & Safaris", "Winter Sports", "Water Sports", "Hiking & Trekking",
        "Luxury Experiences", "Budget Travel", "Solo Travel", "Family Activities",
        "Romantic Getaways", "Educational Tours", "Volunteer Opportunities",
        "Eco Tourism", "Urban Exploration", "Rural Tourism", "Other"
    ]
    
    selected_interests = st.multiselect(
        "Interests",
        predefined_interests,
        ["Culture & History", "Food & Cuisine"],
        help="Select your travel interests"
    )
    
    # Show text input for custom interests if "Other" is selected
    if "Other" in selected_interests:
        custom_interest = st.text_input(
            "Enter your custom interest",
            placeholder="e.g., Street Art Photography",
            help="Type in your specific interest"
        )
        if custom_interest:
            # Remove "Other" and add the custom interest
            selected_interests.remove("Other")
            selected_interests.append(custom_interest)
    
    interests = selected_interests
    
    # Language preference
    language = st.selectbox(
        "Preferred Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese"],
        help="Select your preferred language for the travel plan"
    )

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
st.title("🌎 AI Trip Saver")
st.markdown("Your intelligent AI-powered travel planning solution")

# Create organized tabs for different views
tab1, tab2, tab3 = st.tabs(["Plan Generator", "Budget Analysis", "🏀 LeBron's Travel Assistant"])

# Initialize tab selection in session state
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = 0

with tab1:
    if st.button("Generate Travel Plan", type="primary"):
        if starting_location and destinations and len(destinations) == num_destinations and interests and return_city:
            # Calculate budget estimates
            duration = (end_date - start_date).days + 1
            budget_data = calculate_budget_estimate(duration, budget, " to ".join(destinations))
            
            # Generate and display travel plan
            with st.spinner('Crafting your personalized travel plan...'):
                travel_plan = generate_travel_plan(starting_location, destinations, start_date, end_date, budget, interests, return_city)
                
                # Save to history
                st.session_state.travel_history.append({
                    "starting_location": starting_location,
                    "destination": " to ".join(destinations),
                    "return_city": return_city,
                    "date": start_date.strftime("%Y-%m-%d"),
                    "duration": duration,
                    "budget": budget,
                    "estimated_cost": budget_data["total_estimate"]
                })
            
            # Store travel plan in session state
            st.session_state.current_travel_plan = travel_plan
            
            # Display the plan
            st.markdown(travel_plan)
            
            # Enhanced download options
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="📥 Download as Text",
                    data=travel_plan,
                    file_name=f"travel_plan_{'-'.join(destinations).replace(' ', '_')}.txt",
                    mime="text/plain"
                )
            with col2:
                try:
                    pdf_data = create_pdf(travel_plan, " to ".join(destinations))
                    st.download_button(
                        label="📥 Download as PDF",
                        data=pdf_data,
                        file_name=f"travel_plan_{'-'.join(destinations).replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error creating PDF: {str(e)}")
            with col3:
                if st.button("📅 Add to Google Calendar"):
                    try:
                        add_to_google_calendar(
                            st.session_state.current_travel_plan,
                            datetime.combine(start_date, datetime.min.time()),
                            datetime.combine(end_date, datetime.min.time()),
                            destinations
                        )
                    except Exception as e:
                        st.error(f"Failed to add to Google Calendar: {str(e)}")
        else:
            st.error("Please complete all required fields to generate your travel plan.")

    # Add floating LeBron navigator
    st.markdown("""
        <div class="floating-lebron-nav" onclick="document.getElementsByClassName('st-emotion-cache-1v7p1xi e1nzilvr5')[2].click();">
            <div class="lebron-tooltip">Chat with LeBron using the Lebron Travel Assistant Tab</div>
            <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png" alt="Chat with LeBron using the Lebron Travel Assistant Tab">
        </div>
    """, unsafe_allow_html=True)

with tab2:
    if len(st.session_state.travel_history) > 0:
        df = pd.DataFrame(st.session_state.travel_history)
        
        # Enhanced budget visualization
        st.subheader("Trip Cost Comparison")
        fig = px.bar(
            df, 
            x="destination", 
            y="estimated_cost", 
            color="budget", 
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
            )
        )
        
        st.plotly_chart(
            fig, 
            use_container_width=True, 
            theme="streamlit",
            config={'displayModeBar': True}
        )
        
        # Enhanced trip duration analysis
        st.subheader("Trip Duration Analysis")
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
            hovermode='closest'
        )
        
        st.plotly_chart(
            fig2, 
            use_container_width=True, 
            theme="streamlit",
            key="duration_plot",
            on_select="rerun",
            selection_mode=["box", "lasso"]
        )
        
        # Professional summary statistics
        st.subheader("Summary Statistics")
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
        
        # Enhanced interactive table
        st.subheader("Detailed Trip History")
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
        
    else:
        st.info("Generate travel plans to view detailed budget analysis.")

with tab3:
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        st.image("https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png", width=60)
    with col2:
        st.subheader("🏀 Chat with LeBron")
    
    st.markdown("Hey young fella! I'm LeBron, and I'm here to help you plan your next adventure. What's on your mind? 👑")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Update the chat input placeholder
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

    # Add clear chat button
    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# Enhanced footer with professional tips
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💡 Professional Travel Tips")
    st.markdown("""
    <div class="tip-box">
    - Research destination-specific entry requirements and travel regulations
    - Consider booking accommodations in advance for better rates
    - Monitor travel advisories and local health guidelines
    - Invest in comprehensive travel insurance for international trips
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🔍 Support & Resources")
    st.markdown("""
    <div class="tip-box">
    - Technical Support: support@aitravelplanner.com
    - Knowledge Base: help.aitravelplanner.com
    - Travel Community: community.aitravelplanner.com
    - Latest Updates: @AITravelPro
    </div>
    """, unsafe_allow_html=True)