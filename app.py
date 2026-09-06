import streamlit as st
import streamlit.components.v1 as components
import os
import time
from config import Config
from modules.graph_db import GraphDatabaseConnector
from modules.text_extractor import TextExtractor
from modules.doc_manager import DocumentManager
from modules.graph_visualizer import GraphVisualizer
from modules.qa_engine import QAEngine

# Streamlit Page Config
st.set_page_config(
    page_title="Personal AI Knowledge Graph",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI Design
STYLING_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Clean Light Theme */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.2);
    }
    
    .header-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        font-size: 15px;
        opacity: 0.9;
        margin-top: 6px;
    }
    
    /* Metrics Row Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #4F46E5;
    }
    
    .metric-lbl {
        font-size: 13px;
        color: #64748B;
        font-weight: 500;
        margin-top: 4px;
    }
    
    /* Concept Detail Drawer */
    .detail-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-top: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .type-badge {
        display: inline-block;
        background: #EEF2FF;
        color: #4F46E5;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin-left: 8px;
    }
    
    .citation-badge {
        display: inline-block;
        background: #F1F5F9;
        color: #334155;
        font-size: 11px;
        font-weight: 500;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid #CBD5E1;
    }
    
    /* Custom Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 8px;
        padding-left: 16px;
        padding-right: 16px;
        font-weight: 600;
    }
</style>
"""

st.markdown(STYLING_CSS, unsafe_allow_html=True)

# Session State Initialization
if "db_connected" not in st.session_state:
    st.session_state.db_connected = False
if "db_error" not in st.session_state:
    st.session_state.db_error = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_concept" not in st.session_state:
    st.session_state.selected_concept = None

# Initialize Database Connector
db = GraphDatabaseConnector()

def test_and_connect_db():
    try:
        db.connect()
        st.session_state.db_connected = True
        st.session_state.db_error = None
    except Exception as e:
        st.session_state.db_connected = False
        st.session_state.db_error = str(e)

test_and_connect_db()

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/brain.png", width=64)
    st.title("Settings & Status")
    
    # Connection Status Widget
    if st.session_state.db_connected:
        st.success("🟢 Neo4j Database Connected")
    else:
        st.error("🔴 Neo4j Disconnected")
        with st.expander("Neo4j Credentials"):
            neo_uri = st.text_input("Neo4j URI", value=Config.NEO4J_URI)
            neo_user = st.text_input("Username", value=Config.NEO4J_USERNAME)
            neo_pass = st.text_input("Password", value=Config.NEO4J_PASSWORD, type="password")
            if st.button("Reconnect Database"):
                db.uri = neo_uri
                db.username = neo_user
                db.password = neo_pass
                test_and_connect_db()
                st.rerun()

    st.markdown("---")
    
    # AI Settings (OpenAI / Groq support)
    st.subheader("🤖 AI Model Provider")
    raw_key = st.text_input(
        "API Key (Groq or OpenAI)", 
        value=Config.OPENAI_API_KEY if Config.OPENAI_API_KEY != "your_openai_api_key_here" else "", 
        type="password",
        help="Supports Groq (gsk_...) and OpenAI (sk-...) API Keys"
    )
    
    if raw_key.strip() and raw_key.strip() != "your_openai_api_key_here":
        st.session_state.api_key = raw_key.strip()
    else:
        st.session_state.api_key = ""

    # Detect Provider & Models
    if st.session_state.api_key.startswith("gsk_"):
        st.info("⚡ Provider Detected: **Groq Cloud**")
        available_models = ["openai/gpt-oss-120b", "groq/compound", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "groq/compound-mini"]
    elif st.session_state.api_key.startswith("sk-"):
        st.info("🤖 Provider Detected: **OpenAI**")
        available_models = ["gpt-4o-mini", "gpt-4o"]
    else:
        if st.session_state.api_key:
            st.info("🌐 Custom Provider")
            available_models = ["groq/compound-mini", "gpt-4o-mini", "gpt-4o"]
        else:
            available_models = ["groq/compound-mini", "gpt-4o-mini"]
            st.warning("🔑 Please enter your Groq (`gsk_...`) or OpenAI (`sk-...`) API key above.")

    model_choice = st.selectbox(
        "Model Name",
        available_models,
        index=0
    )
    st.session_state.model_choice = model_choice

    st.markdown("---")
    
    # Quick Sample Data Loader
    st.subheader("🧪 Demo Dataset")
    if st.button("📥 Load Sample Documents", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Please provide an API Key (Groq or OpenAI) in the sidebar.")
        elif not st.session_state.db_connected:
            st.error("Neo4j is not connected. Please check database status.")
        else:
            with st.spinner(f"Processing sample notes into graph using {st.session_state.model_choice}..."):
                try:
                    sample_txt_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_ai_notes.txt")
                    if os.path.exists(sample_txt_path):
                        with open(sample_txt_path, "rb") as f:
                            content = f.read()
                        res = DocumentManager.process_document(
                            file_name="sample_ai_notes.txt",
                            file_bytes=content,
                            db=db,
                            api_key=st.session_state.api_key,
                            model_name=st.session_state.model_choice
                        )
                        st.success(f"Sample data loaded! Extracted {res['concepts_extracted']} concepts.")
                        time.sleep(1)
                        st.rerun()
                except Exception as ex:
                    st.error(f"Error loading sample data: {str(ex)}")

# Main Application Banner
st.markdown("""
<div class="header-card">
    <div class="header-title">Personal AI Knowledge Graph</div>
    <div class="header-subtitle">Upload your documents, extract interconnected concepts, explore interactive graphs, and ask grounded AI questions with citations.</div>
</div>
""", unsafe_allow_html=True)

# Metrics Header Bar
if st.session_state.db_connected:
    try:
        stats = db.get_graph_stats()
    except Exception:
        stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}
else:
    stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_docs"]}</div><div class="metric-lbl">Uploaded Documents</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_concepts"]}</div><div class="metric-lbl">Deduplicated Concepts</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_relationships"]}</div><div class="metric-lbl">Connected Relationships</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["graph_density"]}</div><div class="metric-lbl">Avg Connections / Node</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab_explorer, tab_ingest, tab_qa = st.tabs([
    "🔍 Graph Explorer", 
    "📁 Document Ingestion & Registry", 
    "💬 Grounded Q&A Assistant"
])

# ----------------------------------------------------
# TAB 1: INTERACTIVE GRAPH EXPLORER
# ----------------------------------------------------
with tab_explorer:
    if not st.session_state.db_connected:
        st.warning("⚠️ Neo4j Database is not connected. Start your Neo4j instance to explore the graph.")
    else:
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
        with col_ctrl1:
            search_query = st.text_input("🔎 Search Concepts & Descriptions", placeholder="e.g. Gradient Descent, Transformer, Robotics...")
        with col_ctrl2:
            all_types = db.get_all_entity_types()
            selected_type = st.selectbox("Filter Entity Type", all_types)
        with col_ctrl3:
            max_nodes = st.slider("Max Display Nodes", min_value=20, max_value=500, value=150, step=10)

        graph_data = db.get_graph_data(search_query=search_query, entity_type_filter=selected_type, limit=max_nodes)
        
        if not graph_data["nodes"]:
            st.info("💡 No concepts found in graph. Upload documents in the 'Document Ingestion' tab or click 'Load Sample Documents' in the sidebar.")
        else:
            col_graph, col_panel = st.columns([3, 1])
            
            with col_graph:
                st.subheader("Interactive Knowledge Network")
                st.caption("Drag nodes to position, scroll to zoom, hover for details.")
                html_code = GraphVisualizer.generate_html(graph_data, height="600px")
                components.html(html_code, height=620, scrolling=False)

            with col_panel:
                st.subheader("Concept Detail Inspector")
                node_names = [n["label"] for n in graph_data["nodes"]]
                norm_map = {n["label"]: n["id"] for n in graph_data["nodes"]}
                
                selected_label = st.selectbox("Select Concept to Inspect", ["-- Choose Concept --"] + sorted(node_names))
                
                if selected_label and selected_label != "-- Choose Concept --":
                    norm_name = norm_map[selected_label]
                    details = db.get_concept_details(norm_name)
                    
                    if details:
                        st.markdown(f"### {details['name']}")
                        st.markdown(f"<span class='type-badge'>{details['entity_type']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Description:** {details['description']}")
                        
                        st.markdown("#### 📄 Source Documents")
                        for d in details['source_docs']:
                            st.markdown(f"- `{d}`")
                            
                        st.markdown("#### 📍 Page Citations")
                        for p in details['source_pages']:
                            st.markdown(f"<span class='citation-badge'>{p}</span>", unsafe_allow_html=True)
                            
                        st.markdown("#### 🔗 Connected Concepts")
                        if details['outgoing_relationships']:
                            for rel in details['outgoing_relationships']:
                                st.markdown(f"➔ **{rel['type']}** ➔ `{rel['target']}`")
                        if details['incoming_relationships']:
                            for rel in details['incoming_relationships']:
                                st.markdown(f"⬅ **{rel['type']}** ⬅ `{rel['source']}`")

# ----------------------------------------------------
# TAB 2: DOCUMENT INGESTION & MANAGEMENT
# ----------------------------------------------------
with tab_ingest:
    st.subheader("Upload PDF or TXT Notes")
    
    uploaded_files = st.file_uploader(
        "Choose PDF or TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="Upload study notes, research papers, or documentation."
    )

    if uploaded_files:
        if st.button("🚀 Extract Concepts & Build Graph", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your Groq or OpenAI API key in the sidebar settings first.")
            elif not st.session_state.db_connected:
                st.error("Neo4j database is not connected.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Processing '{file.name}' ({idx + 1}/{len(uploaded_files)}) using {st.session_state.model_choice}...")
                    try:
                        file_bytes = file.read()
                        result = DocumentManager.process_document(
                            file_name=file.name,
                            file_bytes=file_bytes,
                            db=db,
                            api_key=st.session_state.api_key,
                            model_name=st.session_state.model_choice
                        )
                        if result["status"] == "DUPLICATE":
                            st.warning(result["message"])
                        else:
                            st.success(result["message"])
                    except Exception as e:
                        st.error(f"Failed to process '{file.name}': {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("Ingestion completed!")
                time.sleep(1)
                st.rerun()

    st.markdown("---")
    st.subheader("Document Registry")
    
    if st.session_state.db_connected:
        docs = db.get_all_documents()
        if docs:
            for doc in docs:
                col_d1, col_d2, col_d3, col_d4 = st.columns([3, 1, 1, 1])
                with col_d1:
                    st.markdown(f"📄 **{doc['doc_name']}**")
                    st.caption(f"Added: {doc['created_at'][:10] if len(doc['created_at'])>=10 else doc['created_at']}")
                with col_d2:
                    st.markdown(f"**{doc['page_count']}** Page(s)")
                with col_d3:
                    st.markdown(f"**{doc['concept_count']}** Concepts")
                with col_d4:
                    if st.button("🗑️ Delete", key=f"del_{doc['doc_name']}"):
                        db.delete_document(doc['doc_name'])
                        st.success(f"Deleted {doc['doc_name']}")
                        st.rerun()
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.info("No documents currently stored in graph.")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🚨 Danger Zone: Clear Entire Knowledge Graph"):
        st.write("This will delete all stored concepts, relationships, and document references in Neo4j.")
        confirm_check = st.checkbox("I understand this action cannot be undone")
        if st.button("Clear Graph Database", type="primary", disabled=not confirm_check):
            if st.session_state.db_connected:
                db.reset_graph()
                st.success("Knowledge graph has been completely reset.")
                st.rerun()

# ----------------------------------------------------
# TAB 3: GROUNDED QUESTION ANSWERING
# ----------------------------------------------------
with tab_qa:
    st.subheader("Grounded Knowledge Assistant")
    st.caption("Ask questions about your uploaded documents. Answers are strictly grounded in your knowledge graph and cite exact source pages.")

    # Preset Sample Prompts
    st.markdown("**Example Questions:**")
    preset_cols = st.columns(3)
    preset_q = None
    with preset_cols[0]:
        if st.button("What concepts are connected to machine learning?"):
            preset_q = "What concepts are connected to machine learning?"
    with preset_cols[1]:
        if st.button("Explain Gradient Descent & Neural Networks"):
            preset_q = "Explain the relationship between gradient descent and neural networks."
    with preset_cols[2]:
        if st.button("Summarize main topics in my notes"):
            preset_q = "Summarize everything I know about main topics in my uploaded notes."

    # Render Chat History
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "citations" in message and message["citations"]:
                st.markdown("**Sources Cited:**")
                for cite in message["citations"]:
                    st.markdown(f"<span class='citation-badge'>📍 {cite['citation']} ({cite['concept']})</span>", unsafe_allow_html=True)

    # Question Input
    user_input = st.chat_input("Ask a question about your knowledge graph...")
    query_to_process = preset_q or user_input

    if query_to_process:
        if not st.session_state.api_key:
            st.error("Please enter your Groq or OpenAI API Key in the sidebar.")
        elif not st.session_state.db_connected:
            st.error("Neo4j Database is not connected.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Searching Knowledge Graph & generating grounded answer..."):
                    answer, citations = QAEngine.answer_question(
                        user_question=query_to_process,
                        db=db,
                        api_key=st.session_state.api_key,
                        model_name=st.session_state.model_choice
                    )
                    st.markdown(answer)
                    if citations:
                        st.markdown("**Sources Cited:**")
                        for cite in citations:
                            st.markdown(f"<span class='citation-badge'>📍 {cite['citation']} ({cite['concept']})</span>", unsafe_allow_html=True)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })
