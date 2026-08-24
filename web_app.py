import streamlit as st
import pandas as pd
import time
import json
from pipeline import TriagePipeline

# Page Config
st.set_page_config(page_title="AI Triage Engine", layout="wide")

# Cache the pipeline so it doesn't reload the models on every button click
@st.cache_resource
def load_pipeline():
    return TriagePipeline()

pipeline = load_pipeline()

# Header
st.title("Autonomous Support Triage")
st.markdown("AI-driven priority routing with deterministic RAG & DB Tool Calling.")

# Tabs for UX
tab1, tab2 = st.tabs(["Single Message Test", "Batch Upload Dataset"])

# ==========================================
# TAB 1: SINGLE MESSAGE
# ==========================================
with tab1:
    st.subheader("Live Triage Simulator")
    
    user_input = st.text_area("Customer Message:", height=100, placeholder="Type a difficult, sarcastic, or messy message here...")
    
    if st.button("Run Triage", type="primary"):
        if user_input.strip():
            with st.spinner("Analyzing routing logic and querying tools..."):
                start_time = time.time()
                decision = pipeline.run(user_input)
                latency = time.time() - start_time
            
            # Top Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Priority", decision["priority"])
            col2.metric("Category", decision["category"])
            
            human_color = "red" if decision["needs_human"] else "green"
            col3.markdown(f"**Needs Human:** :{human_color}[{'YES' if decision['needs_human'] else 'NO'}]")
            col4.metric("Confidence", f"{decision['confidence']}%")
            
            # Results Cards
            st.info(f"**Summary:** {decision['summary']}")
            st.success(f"**Suggested Action:** {decision['suggested_action']}")
            
            if decision.get("tools_triggered", "None") != "None":
                st.warning(f"**Tools Used:** {decision['tools_triggered']}")
                
            st.caption(f"Latency: {latency:.2f} seconds")
        else:
            st.error("Please enter a message to triage.")

# ==========================================
# TAB 2: BATCH DATASET UPLOAD
# ==========================================
with tab2:
    st.subheader("Dataset Processor")
    uploaded_file = st.file_uploader("Drop a .csv, .json, or .txt file here", type=["csv", "json", "txt"])
    
    if uploaded_file is not None:
        if st.button("Run Batch Pipeline", type="primary"):
            messages = []
            
            # Universal File Parser
            if uploaded_file.name.endswith('.txt'):
                messages = [line.decode("utf-8").strip() for line in uploaded_file if line.decode("utf-8").strip()]
            
            elif uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                col_name = next((c for c in df.columns if c.lower() in ['message', 'text', 'body', 'input', 'content']), df.columns[0])
                messages = df[col_name].dropna().astype(str).tolist()
            
            elif uploaded_file.name.endswith('.json'):
                data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                if isinstance(data, list):
                    if data and isinstance(data[0], dict):
                        key = next((k for k in ['message', 'text', 'body', 'input', 'content'] if k in data[0]), list(data[0].keys())[0])
                        messages = [item[key] for item in data if key in item]
                    else:
                        messages = [str(item) for item in data]
            
            st.write(f"**Loaded {len(messages)} messages. Processing...**")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            start_time = time.time()
            
            # Process Loop
            for i, msg in enumerate(messages):
                decision = pipeline.run(msg)
                
                # Format for the datatable
                row = {
                    "Message": msg[:50] + "..." if len(msg) > 50 else msg,
                    "Pri": decision["priority"],
                    "Cat": decision["category"],
                    "Human?": "YES" if decision["needs_human"] else "NO",
                    "Tools": decision.get("tools_triggered", "None"),
                    "Action": decision["suggested_action"]
                }
                results.append(row)
                
                progress_bar.progress((i + 1) / len(messages))
                status_text.text(f"Processed {i + 1}/{len(messages)}...")
                
            total_time = time.time() - start_time
            st.success(f"Batch completed in {total_time:.2f}s! (~{total_time/len(messages):.2f}s/message)")
            
            # Display interactive dataframe
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)
            
            # Download Button
            csv_export = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Triage CSV",
                data=csv_export,
                file_name="triage_batch_results.csv",
                mime="text/csv"
            )