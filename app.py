import streamlit as st
import os
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# Configure page
st.set_page_config(
    page_title="AI Travel Planner Pro",
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@aitravelplanner.com',
        'Report a bug': 'mailto:bugs@aitravelplanner.com',
        'About': 'AI Travel Planner Pro - Your personal travel assistant'
    }
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    .stProgress .st-bo {
        background-color: #1f77b4;
    }
    .sidebar-content {
        padding: 1rem;
    }
    h1 {
        color: #1E88E5;
    }
    .tip-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .plot-container {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'travel_history' not in st.session_state:
    st.session_state.travel_history = []

# Configure Gemini API
os.environ["GEMINI_API_KEY"] = "AIzaSyAE1UNYk-qqRezzLnSAwDYgTpKVOvYyW_4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create Gemini model configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config
)

def calculate_budget_estimate(duration: int, daily_budget: int, destination: str):
    # Calculate total estimate based on daily budget and duration
    total_estimate = daily_budget * duration
    
    # Calculate breakdown based on typical travel expense ratios
    breakdown = {
        "accommodation": daily_budget * 0.4,  # 40% for accommodation
        "food": daily_budget * 0.2,           # 20% for food
        "activities": daily_budget * 0.2,     # 20% for activities
        "transportation": daily_budget * 0.2   # 20% for transportation
    }
    
    return {
        "daily_total": daily_budget,
        "total_estimate": total_estimate,
        "breakdown": breakdown
    }

def generate_travel_plan(destinations: list, start_date: datetime, end_date: datetime, budget: str, interests: list):
    duration = (end_date - start_date).days + 1
    destinations_str = " → ".join(destinations)
    
    prompt = f"""
    Create a detailed multi-destination travel plan:
    Destinations: {destinations_str}
    Travel Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({duration} days)
    Budget Level: {budget}
    Interests: {', '.join(interests)}
    
    Please provide the response in the following structured format:
    
    # Overview
    [Brief introduction about the trip and why these destinations work well together]
    
    # Weather and Best Time to Visit
    [Information about weather during the travel period for each destination]
    
    # Multi-City Itinerary
    [Detailed day-by-day breakdown including travel between destinations]
    
    # Accommodation Recommendations
    [List of recommended hotels for {budget} budget in each city]
    
    # Transportation
    [Detailed transportation options between cities and within each destination]
    
    # Local Customs & Etiquette
    [Important cultural notes and etiquette tips for each destination]
    
    # Must-Try Local Cuisine
    [List of recommended local dishes for each destination]
    
    # Safety Tips
    [Important safety information and emergency contacts for each location]
    
    # Estimated Costs
    [Detailed cost breakdown for {budget} budget including inter-city travel]
    
    # Packing Recommendations
    [Season-appropriate packing list for all destinations]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating travel plan: {str(e)}"

# Sidebar for user inputs
with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/airplane-mode-on.png", width=100)
    st.title("Trip Parameters")
    
    # Multiple destination input
    destinations = []
    num_destinations = st.number_input("Number of Destinations", min_value=1, max_value=5, value=1)
    
    for i in range(num_destinations):
        dest = st.text_input(f"Destination {i+1}", placeholder="e.g., Tokyo, Japan", key=f"dest_{i}")
        if dest:
            destinations.append(dest)
    
    # Date selection
    start_date = st.date_input("Start Date", min_value=datetime.today())
    end_date = st.date_input("End Date", min_value=start_date)
    
    budget = st.slider(
        "Daily Budget (USD)",
        min_value=0,
        max_value=2000,
        value=500,
        step=50,
        format="$%d"
    )
    
    interests = st.multiselect(
        "Interests",
        ["Culture & History", "Food & Cuisine", "Nature & Outdoors", 
         "Shopping", "Art & Museums", "Nightlife", "Adventure Sports",
         "Local Experiences", "Photography", "Architecture"],
        ["Culture & History", "Food & Cuisine"]
    )
    
    language = st.selectbox(
        "Preferred Language",
        ["English", "Spanish", "French", "German", "Japanese", "Chinese"]
    )

# Add this function for PDF conversion
def create_pdf(travel_plan: str, destination: str) -> bytes:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Travel Plan - {destination}', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # Split text into lines and add to PDF
    lines = travel_plan.split('\n')
    for line in lines:
        if line.startswith('#'):  # Handle headers
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, line.replace('#', '').strip(), 0, 1)
            pdf.set_font('Arial', '', 12)
        else:
            pdf.multi_cell(0, 10, line)
    
    return pdf.output(dest='S').encode('latin-1')

# Main content area
st.title("🌎 AI Travel Planner Pro")
st.markdown("Your personal AI-powered travel assistant")

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Plan Generator", "Budget Analysis", "Travel History"])

with tab1:
    if st.button("Generate Travel Plan", type="primary"):
        if destinations and len(destinations) == num_destinations and interests:
            # Calculate budget estimates
            duration = (end_date - start_date).days + 1
            budget_data = calculate_budget_estimate(duration, budget, " → ".join(destinations))
            
            # Generate and display travel plan
            with st.spinner('Crafting your perfect travel plan...'):
                travel_plan = generate_travel_plan(destinations, start_date, end_date, budget, interests)
                
                # Save to history
                st.session_state.travel_history.append({
                    "destination": " → ".join(destinations),
                    "date": start_date.strftime("%Y-%m-%d"),
                    "duration": duration,
                    "budget": budget,
                    "estimated_cost": budget_data["total_estimate"]
                })
            
            # Display the plan
            st.markdown(travel_plan)
            
            # Download options
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
                    pdf_data = create_pdf(travel_plan, " → ".join(destinations))
                    st.download_button(
                        label="📥 Download as PDF",
                        data=pdf_data,
                        file_name=f"travel_plan_{'-'.join(destinations).replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error creating PDF: {str(e)}")
        else:
            st.error("Please fill in all required fields")

with tab2:
    if len(st.session_state.travel_history) > 0:
        df = pd.DataFrame(st.session_state.travel_history)
        
        # Budget visualization with improved styling
        st.subheader("Trip Cost Comparison")
        fig = px.bar(
            df, 
            x="destination", 
            y="estimated_cost", 
            color="budget", 
            title="Estimated Costs by Destination",
            template="streamlit",  # Use streamlit template
            labels={
                "destination": "Destination",
                "estimated_cost": "Estimated Cost ($)",
                "budget": "Budget Level"
            }
        )
        
        # Update layout with better styling
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
        
        # Display the chart with proper configuration
        st.plotly_chart(
            fig, 
            use_container_width=True, 
            theme="streamlit",
            config={'displayModeBar': True}
        )
        
        # Trip duration analysis with improved styling
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
                "estimated_cost": "Estimated Cost ($)",
                "destination": "Destination"
            }
        )
        
        # Update scatter plot layout
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
        
        # Add interactive selection
        st.plotly_chart(
            fig2, 
            use_container_width=True, 
            theme="streamlit",
            key="duration_plot",
            on_select="rerun",
            selection_mode=["box", "lasso"]
        )
        
        # Add summary statistics with improved styling
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
                "Average Cost", 
                f"${df['estimated_cost'].mean():,.2f}",
                delta=f"${df['estimated_cost'].std():,.2f} σ",
                help="Average trip cost (with standard deviation)"
            )
        
        with stats_cols[3]:
            most_visited = df['destination'].mode().iloc[0]
            st.metric(
                "Most Popular Destination",
                most_visited,
                help="Most frequently planned destination"
            )
        
        # Add interactive table with sorting
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
                    "Estimated Cost",
                    format="$%.2f",
                ),
                "duration": st.column_config.NumberColumn(
                    "Duration",
                    format="%d days",
                ),
            }
        )
        
    else:
        st.info("Generate some travel plans to see budget analysis!")

with tab3:
    if len(st.session_state.travel_history) > 0:
        st.subheader("Your Travel History")
        st.dataframe(pd.DataFrame(st.session_state.travel_history))
    else:
        st.info("Your travel history will appear here once you generate some plans!")

# Footer with tips and information
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💡 Pro Tips")
    st.markdown("""
    <div class="tip-box">
    - Use specific destinations for more accurate plans
    - Consider shoulder seasons for better deals
    - Check visa requirements and travel advisories
    - Consider travel insurance for international trips
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🔍 Need Help?")
    st.markdown("""
    <div class="tip-box">
    - Contact support: support@aitravelplanner.com
    - Visit our FAQ page
    - Join our travel community
    - Follow us on social media for travel tips
    </div>
    """, unsafe_allow_html=True)
