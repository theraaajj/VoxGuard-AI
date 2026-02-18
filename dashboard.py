import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import time

# Import backend functions
from main import run_voxguard 
from components.memory import query_memory
from components.intelligence import answer_user_query
from components.utils import save_config, load_config

# Database Connection
DATABASE_URL = "sqlite:///./voxguard.db"
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="VoxGuard AI", page_icon="🛡️", layout="wide")

# --- SIDEBAR: CONTROL ---
with st.sidebar:
    st.header("🛡️ VoxGuard Control")
    st.markdown("---")
    
    st.subheader("Process New Video")
    video_url = st.text_input("YouTube URL", placeholder="https://youtube.com/...")
    
    if st.button("🚀 Activate Agent", type="primary"):
        if not video_url:
            st.error("Please enter a URL first.")
        else:
            with st.status("🤖 Agent Active... Please wait.", expanded=True) as status:
                st.write("1️⃣ Ingesting Audio Stream...")
                try:
                    run_voxguard(video_url)
                    status.update(label="✅ Mission Complete!", state="complete", expanded=False)
                    st.success("Analysis finished! Refreshing data...")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Mission Failed: {e}")
                    status.update(label="❌ Error", state="error")

    st.markdown("---")
    try:
        df = pd.read_sql("SELECT * FROM video_memories ORDER BY processed_at DESC", engine)
        st.metric("Total Videos Processed", len(df))
        if not df.empty:
            avg_trust = df['avg_confidence'].mean()
            st.metric("Global Trust Score", f"{avg_trust:.2f}")
    except:
        df = pd.DataFrame()

st.title("🛡️ VoxGuard Intelligence Dashboard")

# --- TABS ---
# Added Settings Tab
tab1, tab2, tab3 = st.tabs(["📊 Intelligence Feed", "🧠 Neural Search", "⚙️ Settings"])

# TAB 1: FEED
with tab1:
    if df.empty:
        st.info("No data yet. Configure settings or process a video.")
    
    for index, row in df.iterrows():
        # Display Real Video Title
        with st.expander(f"{row['title']} (Trust: {row['avg_confidence']})"):
            if row['is_flagged']:
                st.error("⚠️ Acoustic Anomalies Detected")
            st.markdown(row['summary_report'])
            st.caption(f"ID: {row['id']} | {row['processed_at']}")

# TAB 2: SEARCH
with tab2:
    st.header("Search the Agent's Memory")
    query = st.text_input("Ask a question about your videos:", placeholder="What is the future of AI?")
    if query:
        with st.spinner("Analyzing neural pathways..."):
            results = query_memory(query, n_results=5)
            if not results['documents']:
                st.warning("No memories found.")
            else:
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                answer = answer_user_query(query, docs)
                st.markdown("### 🤖 Agent Answer")
                st.success(answer)
                st.markdown("---")
                st.subheader("📄 Evidence Sources")
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    # Use .get with default to handle missing keys
                    title = meta.get('title', 'Unknown Video')
                    ts = meta.get('start_time', 0)
                    with st.expander(f"Reference: {title} (at {ts:.1f}s)"):
                        st.markdown(f"> *\"{doc}\"*")
                        if meta.get('is_flagged'):
                            st.warning("⚠️ Low Confidence Segment")

# TAB 3: SETTINGS (New Feature)
with tab3:
    st.header("🤖 Agent Configuration")
    
    # Load existing config
    current_conf = load_config()
    
    with st.form("settings_form"):
        st.subheader("Daily Monitoring")
        st.markdown("Enter the Channel IDs you want to watch (one per line or comma separated).")
        
        # Helper link for finding IDs
        st.markdown("[Find Channel IDs here](https://commentpicker.com/youtube-channel-id.php)")
        
        # Join list into string for display
        default_channels = ", ".join(current_conf.get("channels", []))
        channels_input = st.text_area("Target Channel IDs", value=default_channels)
        
        st.subheader("Email Notifications")
        email_input = st.text_input("Your Email Address", value=current_conf.get("email", ""))
        pass_input = st.text_input("Gmail App Password", type="password", value=current_conf.get("smtp_password", ""))
        
        if st.form_submit_button("💾 Save Configuration"):
            save_config(channels_input, email_input, pass_input)
            st.success("Settings saved! Restart 'monitor.py' to apply changes.")

