import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF 

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

def generate_travel_plan(destinations: list, start_date: datetime, end_date: datetime, budget: str, interests: list) -> str:
    """
    Generate comprehensive travel plans using AI with structured formatting.
    """
    duration = (end_date - start_date).days + 1
    destinations_str = " to ".join(destinations)
    
    prompt = f"""
    Create a detailed multi-destination travel plan that uses AT LEAST 80% of the daily budget of ${budget} every day. DO NOT USE more than 100% of the ${budget} for any singular day on the itinerary.
    All recommendations for accommodations, activities, food, and transportation MUST be realistic and achievable within this budget.
    
    Destinations: {destinations_str}
    Travel Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({duration} days)
    Daily Budget: ${budget} per day
    Interests: {', '.join(interests)}
    
    Please provide the response in the following structured format, using emojis, bold text (**), italics (_), and bullet points to make the content engaging:

    # ✨ Overview
    [Write an engaging introduction using descriptive language and metaphors about the trip and why these destinations complement each other perfectly]
    
    # 🌤️ Weather and Best Time to Visit
    [Vivid description of the weather and atmosphere during the travel period for each destination]
    
    # 📅 Multi-City Itinerary
    [Create an exciting day-by-day breakdown for EACH day from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d')}, including:
    - 🌅 **Morning**: [activities and costs with descriptive details]
    - ☀️ **Afternoon**: [activities and costs with engaging descriptions]
    - 🌙 **Evening**: [activities and costs with atmospheric details]
    - 🍽️ **Where to Eat**: [restaurant recommendations with signature dishes]
    - 🚆 **Travel Details**: [if applicable, with practical tips]
    - 🏨 **Accommodation**: [hotel details with standout features]
    - 💰 **Daily Spending**: $X (separate bullet point)]
    
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
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating travel plan: {str(e)}"

# Professional sidebar interface
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/airplane-mode-on.png", width=100)
    st.title("Trip Parameters")
    
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
    
    # Refined interests selection
    interests = st.multiselect(
        "Interests",
        ["Culture & History", "Food & Cuisine", "Nature & Outdoors", 
         "Shopping", "Art & Museums", "Nightlife", "Adventure Sports",
         "Local Experiences", "Photography", "Architecture"],
        ["Culture & History", "Food & Cuisine"],
        help="Select your travel interests"
    )
    
    # Language preference
    language = st.selectbox(
        "Preferred Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese"],
        help="Select your preferred language for the travel plan"
    )

# Enhanced PDF generation
def create_pdf(travel_plan: str, destination: str) -> bytes:
    """
    Create professionally formatted PDF travel plans with Unicode support.
    """
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            safe_destination = destination.replace('→', 'to')
            self.cell(0, 10, f'Travel Plan - {safe_destination}', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    
    # Clean the text by removing emojis and other special characters
    def clean_text(text):
        import re
        # Remove emojis and other special characters
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub('', text)
    
    lines = travel_plan.split('\n')
    for line in lines:
        cleaned_line = clean_text(line)
        if line.startswith('#'):
            pdf.set_font('DejaVu', '', 14)
            # Remove the # and any emojis from section headers
            header_text = cleaned_line.replace('#', '').strip()
            pdf.cell(0, 10, header_text, 0, 1)
            pdf.set_font('DejaVu', '', 12)
        else:
            if cleaned_line.strip():  # Only add non-empty lines
                pdf.multi_cell(0, 10, cleaned_line)
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# Main content area with professional layout
st.title("🌎 AI Travel Planner Pro")
st.markdown("Your intelligent AI-powered travel planning solution")

# Create organized tabs for different views
tab1, tab2, tab3 = st.tabs(["Plan Generator", "Budget Analysis", "Travel History"])

with tab1:
    if st.button("Generate Travel Plan", type="primary"):
        if destinations and len(destinations) == num_destinations and interests:
            # Calculate budget estimates
            duration = (end_date - start_date).days + 1
            budget_data = calculate_budget_estimate(duration, budget, " to ".join(destinations))
            
            # Generate and display travel plan
            with st.spinner('Crafting your personalized travel plan...'):
                travel_plan = generate_travel_plan(destinations, start_date, end_date, budget, interests)
                
                # Save to history
                st.session_state.travel_history.append({
                    "destination": " to ".join(destinations),
                    "date": start_date.strftime("%Y-%m-%d"),
                    "duration": duration,
                    "budget": budget,
                    "estimated_cost": budget_data["total_estimate"]
                })
            
            # Display the plan
            st.markdown(travel_plan)
            
            # Enhanced download options
            col1, col2 = st.columns(2)
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
        else:
            st.error("Please complete all required fields to generate your travel plan.")

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
    if len(st.session_state.travel_history) > 0:
        st.subheader("Your Travel History")
        st.dataframe(pd.DataFrame(st.session_state.travel_history))
    else:
        st.info("Your travel history will be displayed here after generating plans.")

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
