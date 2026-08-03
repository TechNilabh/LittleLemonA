import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as bg
import json
import urllib.request
from datetime import datetime

st.set_page_config(
    page_title="CP Insight — Streamlit Interactive Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Brutalist Styling for Streamlit
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0f1117;
        color: #f8fafc;
    }
    
    .stSidebar {
        background-color: #161922 !important;
        border-right: 2px solid #262a36 !important;
    }
    
    .metric-card {
        background-color: #161922;
        border: 2px solid #262a36;
        padding: 1.2rem;
        border-radius: 2px;
        margin-bottom: 1rem;
    }

    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 800;
        color: #7c3aed;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("⚡ CP INSIGHT")
st.sidebar.markdown("**Interactive Analytics Dashboard**")
handle = st.sidebar.text_input("Codeforces Handle", value="tourist")
fetch_btn = st.sidebar.button("Fetch Analytics")

@st.cache_data(ttl=600)
def fetch_cf_data(user_handle):
    base_url = "https://codeforces.com/api"
    try:
        req = urllib.request.Request(f"{base_url}/user.info?handles={user_handle}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            info = json.loads(resp.read().decode('utf-8'))['result'][0]

        req = urllib.request.Request(f"{base_url}/user.rating?handle={user_handle}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            ratings = json.loads(resp.read().decode('utf-8'))['result']

        req = urllib.request.Request(f"{base_url}/user.status?handle={user_handle}&from=1&count=500", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            submissions = json.loads(resp.read().decode('utf-8'))['result']

        return info, ratings, submissions, None
    except Exception as e:
        return None, None, None, str(e)

if handle:
    info, ratings, submissions, error = fetch_cf_data(handle)

    if error:
        st.error(f"Failed to fetch data for handle **'{handle}'**: {error}")
    else:
        st.title(f"📊 Analytics for `{info.get('handle')}`")
        
        # Profile Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Current Rating</div>
                <div class="metric-value">{info.get('rating', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Max Rating</div>
                <div class="metric-value">{info.get('maxRating', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Rank</div>
                <div class="metric-value" style="font-size:1.3rem;">{info.get('rank', 'Unrated').title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Contribution</div>
                <div class="metric-value">{info.get('contribution', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

        # 1. Rating History Plotly Chart
        st.subheader("📈 Rating Evolution Over Time")
        if ratings:
            df_ratings = pd.DataFrame(ratings)
            df_ratings['date'] = pd.to_datetime(df_ratings['ratingUpdateTimeSeconds'], unit='s')
            fig_rating = px.line(
                df_ratings, 
                x='date', 
                y='newRating', 
                labels={'newRating': 'Rating', 'date': 'Date'},
                markers=True,
                title="Contest Rating Trajectory"
            )
            fig_rating.update_traces(line_color='#7c3aed', marker=dict(size=6, color='#7c3aed'))
            fig_rating.update_layout(
                paper_bgcolor='#161922',
                plot_bgcolor='#0f1117',
                font=dict(color='#94a3b8', family='JetBrains Mono'),
                xaxis=dict(gridcolor='#262a36'),
                yaxis=dict(gridcolor='#262a36')
            )
            st.plotly_chart(fig_rating, use_container_width=True)

        # 2. Tag Breakdown & Verdict Pie
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🏷️ Problem Solved by Tags")
            tag_counts = {}
            verdicts = {}
            for sub in submissions:
                v = sub.get('verdict', 'UNKNOWN')
                verdicts[v] = verdicts.get(v, 0) + 1

                if v == 'OK':
                    for t in sub.get('problem', {}).get('tags', []):
                        tag_counts[t] = tag_counts.get(t, 0) + 1

            if tag_counts:
                df_tags = pd.DataFrame(list(tag_counts.items()), columns=['Tag', 'Count']).sort_values(by='Count', ascending=False).head(10)
                fig_tags = px.bar(
                    df_tags, 
                    x='Count', 
                    y='Tag', 
                    orientation='h', 
                    color_discrete_sequence=['#7c3aed']
                )
                fig_tags.update_layout(
                    paper_bgcolor='#161922',
                    plot_bgcolor='#0f1117',
                    font=dict(color='#94a3b8', family='JetBrains Mono'),
                    xaxis=dict(gridcolor='#262a36'),
                    yaxis=dict(gridcolor='#262a36', categoryorder='total ascending')
                )
                st.plotly_chart(fig_tags, use_container_width=True)

        with col_right:
            st.subheader("🎯 Submission Verdict Distribution")
            if verdicts:
                df_verdicts = pd.DataFrame(list(verdicts.items()), columns=['Verdict', 'Count'])
                fig_pie = px.pie(
                    df_verdicts, 
                    values='Count', 
                    names='Verdict',
                    color_discrete_sequence=px.colors.sequential.Purples_r
                )
                fig_pie.update_layout(
                    paper_bgcolor='#161922',
                    plot_bgcolor='#0f1117',
                    font=dict(color='#94a3b8', family='JetBrains Mono')
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        # 3. Submissions Data Table
        st.subheader("📋 Recent Submissions Feed")
        table_data = []
        for sub in submissions[:30]:
            p = sub.get('problem', {})
            table_data.append({
                'Contest': p.get('contestId', ''),
                'Index': p.get('index', ''),
                'Name': p.get('name', ''),
                'Rating': p.get('rating', 'N/A'),
                'Verdict': sub.get('verdict', ''),
                'Time': datetime.fromtimestamp(sub.get('creationTimeSeconds', 0)).strftime('%Y-%m-%d %H:%M')
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
