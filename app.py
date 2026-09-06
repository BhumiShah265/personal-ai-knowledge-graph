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

# Custom CSS for Premium Research-Oriented Knowledge Workspace
STYLING_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Warm Off-White Background */
    .stApp {
        background-color: #F9F9FB;
        color: #0F172A;
    }

    /* Top Navigation Header Bar */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    .top-header-left {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .top-header-title {
        font-size: 22px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.4px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .top-header-subtitle {
        font-size: 13px;
        color: #64748B;
        font-weight: 400;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-pill.connected {
        background-color: #F0FDF4;
        color: #15803D;
        border: 1px solid #BBF7D0;
    }

    .status-pill.disconnected {
        background-color: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
    }

    .status-dot.connected {
        background-color: #22C55E;
    }

    .status-dot.disconnected {
        background-color: #EF4444;
    }

    /* Overview Metrics Row */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }

    .metric-tile {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        transition: border-color 0.15s ease;
    }

    .metric-tile:hover {
        border-color: #CBD5E1;
    }

    .metric-tile-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748B;
        margin-bottom: 6px;
    }

    .metric-tile-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.5px;
    }

    .metric-tile-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Workspace Content Cards */
    .workspace-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    .workspace-card-title {
        font-size: 17px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.3px;
        margin-bottom: 4px;
    }

    .workspace-card-desc {
        font-size: 13px;
        color: #64748B;
        margin-bottom: 16px;
    }

    /* Graph Legend Chips */
    .legend-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        padding: 10px 14px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        margin-bottom: 14px;
    }

    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: 600;
        color: #334155;
        padding: 3px 8px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
    }

    .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    /* Concept Inspector Drawer */
    .inspector-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
    }

    .concept-title {
        font-size: 18px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .type-chip {
        display: inline-block;
        background: #F3E8FF;
        color: #7C3AED;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .concept-desc {
        font-size: 13px;
        line-height: 1.55;
        color: #334155;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        margin: 12px 0;
    }

    .citation-tag {
        display: inline-flex;
        align-items: center;
        background: #F1F5F9;
        color: #475569;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        border: 1px solid #CBD5E1;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .rel-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #334155;
        padding: 5px 8px;
        background: #F8FAFC;
        border-radius: 6px;
        margin-bottom: 5px;
        border: 1px solid #F1F5F9;
    }

    .rel-badge {
        font-size: 10px;
        font-weight: 700;
        color: #7C3AED;
        background: #F3E8FF;
        padding: 2px 6px;
        border-radius: 4px;
        text-transform: uppercase;
    }

    /* Document Registry Table Cards */
    .doc-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: border-color 0.15s ease;
    }

    .doc-row:hover {
        border-color: #CBD5E1;
    }

    .doc-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .doc-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: #F3E8FF;
        color: #7C3AED;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
    }

    .doc-name {
        font-size: 14px;
        font-weight: 600;
        color: #0F172A;
    }

    .doc-meta {
        font-size: 12px;
        color: #64748B;
        margin-top: 2px;
    }

    /* Grounded Q&A Assistant Styles */
    .qa-banner {
        background: #FAF5FF;
        border: 1px solid #E9D5FF;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13px;
        color: #6B21A8;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
    }

    .qa-answer-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #7C3AED;
        border-radius: 10px;
        padding: 18px 20px;
        margin: 14px 0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    .qa-answer-text {
        font-size: 14px;
        line-height: 1.65;
        color: #0F172A;
    }

    /* Empty States */
    .empty-state {
        text-align: center;
        padding: 48px 24px;
        background: #FFFFFF;
        border: 1px dashed #CBD5E1;
        border-radius: 14px;
        margin: 20px 0;
    }

    .empty-state-title {
        font-size: 16px;
        font-weight: 700;
        color: #1E293B;
        margin: 12px 0 6px 0;
    }

    .empty-state-desc {
        font-size: 13px;
        color: #64748B;
        max-width: 420px;
        margin: 0 auto;
    }

    /* Tab Styling with Purple Accent */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid #E5E7EB;
        padding-bottom: 4px;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        padding: 0 18px;
        font-weight: 600;
        font-size: 14px;
        color: #64748B;
        background-color: transparent;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background-color: #F3E8FF !important;
        color: #7C3AED !important;
    }

    /* Button Customization */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        padding: 6px 16px;
        transition: all 0.15s ease;
    }

    .stButton>button[kind="primary"] {
        background-color: #7C3AED;
        border-color: #7C3AED;
        color: #FFFFFF;
    }

    .stButton>button[kind="primary"]:hover {
        background-color: #6D28D9;
        border-color: #6D28D9;
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
if "api_key" not in st.session_state:
    st.session_state.api_key = Config.GROK_API_KEY or Config.OPENAI_API_KEY
if "model_choice" not in st.session_state:
    st.session_state.model_choice = Config.LLM_MODEL

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

# ----------------------------------------------------
# SIDEBAR / SETTINGS
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 Knowledge Engine")
    st.caption("Personal Intelligence & Graph RAG Workspace")
    
    st.markdown("---")
    st.markdown("**LLM Provider & Credentials**")
    
    raw_key = st.text_input(
        "API Key", 
        value=Config.GROK_API_KEY if Config.GROK_API_KEY else (Config.OPENAI_API_KEY if Config.OPENAI_API_KEY != "your_openai_api_key_here" else ""), 
        type="password",
        help="Enter Groq (gsk_...) or OpenAI (sk-...) API key."
    )
    
    if raw_key.strip() and raw_key.strip() != "your_openai_api_key_here":
        st.session_state.api_key = raw_key.strip()
    else:
        st.session_state.api_key = ""

    # Provider Detection & Model Options
    if st.session_state.api_key.startswith("gsk_"):
        st.success("⚡ Provider: **Groq Cloud**", icon="⚡")
        available_models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "groq/compound",
            "groq/compound-mini"
        ]
    elif st.session_state.api_key.startswith("sk-"):
        st.success("🤖 Provider: **OpenAI**", icon="🤖")
        available_models = ["gpt-4o-mini", "gpt-4o"]
    else:
        available_models = ["openai/gpt-oss-120b", "gpt-4o-mini"]
        if st.session_state.api_key:
            st.info("🌐 Custom Provider")
        else:
            st.warning("⚠️ Enter your API key above to enable AI extraction.")

    default_model_idx = 0
    if st.session_state.model_choice in available_models:
        default_model_idx = available_models.index(st.session_state.model_choice)

    model_choice = st.selectbox(
        "Model Name",
        available_models,
        index=default_model_idx
    )
    st.session_state.model_choice = model_choice

    st.markdown("---")
    st.markdown("**Database Configuration**")
    if st.session_state.db_connected:
        st.markdown(
            '<div class="status-pill connected"><span class="status-dot connected"></span>Neo4j Connected</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-pill disconnected"><span class="status-dot disconnected"></span>Neo4j Offline</div>',
            unsafe_allow_html=True
        )
        with st.expander("Connection Settings", expanded=True):
            neo_uri = st.text_input("Bolt URI", value=Config.NEO4J_URI)
            neo_user = st.text_input("Username", value=Config.NEO4J_USERNAME)
            neo_pass = st.text_input("Password", value=Config.NEO4J_PASSWORD, type="password")
            if st.button("Reconnect Database", use_container_width=True):
                db.uri = neo_uri
                db.username = neo_user
                db.password = neo_pass
                test_and_connect_db()
                st.rerun()

    st.markdown("---")
    st.markdown("**Quick Actions**")
    if st.button("📥 Load Sample Study Notes", use_container_width=True):
        if not st.session_state.api_key:
            st.error("Please enter an API Key in the sidebar.")
        elif not st.session_state.db_connected:
            st.error("Neo4j database is offline.")
        else:
            with st.spinner(f"Ingesting sample notes using {st.session_state.model_choice}..."):
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
                            model_name=st.session_state.model_choice,
                            force_reprocess=True
                        )
                        st.success(f"Ingested {res['concepts_extracted']} concepts & {res['relationships_extracted']} relationships!")
                        time.sleep(1)
                        st.rerun()
                except Exception as ex:
                    st.error(f"Error loading sample data: {str(ex)}")

    with st.expander("🚨 Danger Zone (Reset Graph)"):
        st.caption("Permanently purge all nodes, relationships, and document references from Neo4j.")
        confirm_check = st.checkbox("Confirm database wipe", key="sidebar_wipe_check")
        if st.button("Reset Knowledge Graph", type="primary", disabled=not confirm_check, use_container_width=True):
            if st.session_state.db_connected:
                db.reset_graph()
                st.success("Knowledge graph reset successfully.")
                st.rerun()

# ----------------------------------------------------
# 1. TOP HEADER BAR
# ----------------------------------------------------
db_pill_html = '<div class="status-pill connected"><span class="status-dot connected"></span>Neo4j Active (bolt://localhost:7687)</div>' if st.session_state.db_connected else '<div class="status-pill disconnected"><span class="status-dot disconnected"></span>Neo4j Disconnected</div>'

st.markdown(f"""
<div class="top-header">
    <div class="top-header-left">
        <div class="top-header-title">
            <span>Personal AI Knowledge Graph</span>
        </div>
        <div class="top-header-subtitle">Explore interconnected domain concepts, provenance, and grounded insights across your notes.</div>
    </div>
    <div>
        {db_pill_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. OVERVIEW METRICS SECTION
# ----------------------------------------------------
if st.session_state.db_connected:
    try:
        stats = db.get_graph_stats()
    except Exception:
        stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}
else:
    stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-tile">
        <div class="metric-tile-label">Indexed Documents</div>
        <div class="metric-tile-value">{stats["total_docs"]}</div>
        <div class="metric-tile-sub">PDF & TXT files</div>
    </div>
    <div class="metric-tile">
        <div class="metric-tile-label">Deduplicated Concepts</div>
        <div class="metric-tile-value">{stats["total_concepts"]}</div>
        <div class="metric-tile-sub">Normalized entities</div>
    </div>
    <div class="metric-tile">
        <div class="metric-tile-label">Extracted Relationships</div>
        <div class="metric-tile-value">{stats["total_relationships"]}</div>
        <div class="metric-tile-sub">Directional edges</div>
    </div>
    <div class="metric-tile">
        <div class="metric-tile-label">Graph Density</div>
        <div class="metric-tile-value">{stats["graph_density"]}</div>
        <div class="metric-tile-sub">Avg connections / node</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# MAIN WORKSPACE TABS
# ----------------------------------------------------
tab_explorer, tab_ingest, tab_qa = st.tabs([
    "🔍 Graph Explorer", 
    "📁 Document Management & Ingestion", 
    "💬 Grounded Q&A Assistant"
])

# ----------------------------------------------------
# TAB 1: MAIN GRAPH EXPLORER
# ----------------------------------------------------
with tab_explorer:
    if not st.session_state.db_connected:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size: 32px;">🔌</div>
            <div class="empty-state-title">Neo4j Database Offline</div>
            <div class="empty-state-desc">Please ensure your Neo4j database service is running and configure connection credentials in the sidebar.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Search & Filter Controls Bar
        col_s1, col_s2, col_s3 = st.columns([2.5, 1.2, 1])
        with col_s1:
            search_query = st.text_input("Search Concepts or Keywords", placeholder="Filter graph by keyword, e.g. Neural Networks, Optimizer, Robotics...", label_visibility="collapsed")
        with col_s2:
            all_types = db.get_all_entity_types()
            selected_type = st.selectbox("Entity Type", all_types, label_visibility="collapsed")
        with col_s3:
            max_nodes = st.slider("Display Limit", min_value=20, max_value=400, value=150, step=10, label_visibility="collapsed")

        # Entity Type Color Legend
        legend_chips_html = "".join([
            f'<div class="legend-chip"><span class="legend-dot" style="background-color: {color};"></span>{etype}</div>'
            for etype, color in Config.ENTITY_COLORS.items() if etype != "DEFAULT"
        ])
        st.markdown(f'<div class="legend-bar"><span style="font-size: 11px; font-weight: 700; color: #64748B; margin-right: 4px;">LEGEND:</span>{legend_chips_html}</div>', unsafe_allow_html=True)

        # Retrieve filtered graph data
        graph_data = db.get_graph_data(search_query=search_query, entity_type_filter=selected_type, limit=max_nodes)
        
        if not graph_data["nodes"]:
            st.markdown("""
            <div class="empty-state">
                <div style="font-size: 36px;">🕸️</div>
                <div class="empty-state-title">No Knowledge Graph Data Found</div>
                <div class="empty-state-desc">Upload documents in the <strong>Document Management</strong> tab or click <strong>Load Sample Study Notes</strong> in the sidebar to build your graph.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col_graph, col_inspector = st.columns([2.6, 1.4])
            
            with col_graph:
                st.caption("Interactive Canvas: Drag nodes to rearrange, scroll to zoom, hover for citations.")
                html_code = GraphVisualizer.generate_html(graph_data, height="680px")
                components.html(html_code, height=700, scrolling=False)

            with col_inspector:
                st.markdown('<div class="workspace-card-title">Concept Inspector</div>', unsafe_allow_html=True)
                st.caption("Select a concept from the knowledge base to inspect its citations, properties, and relationships.")
                
                node_labels = [n["label"] for n in graph_data["nodes"]]
                norm_lookup = {n["label"]: n["id"] for n in graph_data["nodes"]}
                
                selected_label = st.selectbox(
                    "Choose Concept", 
                    ["-- Select a Concept --"] + sorted(node_labels),
                    label_visibility="collapsed"
                )
                
                if selected_label and selected_label != "-- Select a Concept --":
                    norm_id = norm_lookup[selected_label]
                    details = db.get_concept_details(norm_id)
                    
                    if details:
                        type_color = Config.ENTITY_COLORS.get(details.get("entity_type", "CONCEPT"), "#7C3AED")
                        st.markdown(f"""
                        <div class="inspector-card">
                            <div class="concept-title">
                                <span>{details['name']}</span>
                                <span class="type-chip" style="color: {type_color}; background: #F3E8FF;">{details['entity_type']}</span>
                            </div>
                            <div class="concept-desc">{details['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("**📄 Provenance & Sources**")
                        for doc in details['source_docs']:
                            st.markdown(f"- 📁 `{doc}`")
                        
                        st.markdown("**📍 Page Citations**")
                        cites_html = "".join([f'<span class="citation-tag">📍 {p}</span>' for p in details['source_pages']])
                        st.markdown(cites_html, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("**🔗 Connected Knowledge**")
                        if details['outgoing_relationships']:
                            for rel in details['outgoing_relationships']:
                                st.markdown(f"""
                                <div class="rel-item">
                                    <span>➔</span>
                                    <span class="rel-badge">{rel['type']}</span>
                                    <strong>{rel['target']}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                        if details['incoming_relationships']:
                            for rel in details['incoming_relationships']:
                                st.markdown(f"""
                                <div class="rel-item">
                                    <span>⬅</span>
                                    <span class="rel-badge">{rel['type']}</span>
                                    <strong>{rel['source']}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("💡 Tip: Select any concept from the dropdown above to view complete provenance, connected concepts, and source citations.")

# ----------------------------------------------------
# TAB 2: DOCUMENT MANAGEMENT & INGESTION
# ----------------------------------------------------
with tab_ingest:
    col_up1, col_up2 = st.columns([1.5, 1])
    
    with col_up1:
        st.markdown('<div class="workspace-card-title">Upload Documents</div>', unsafe_allow_html=True)
        st.caption("Upload PDF or TXT study notes to automatically extract entities, build relationships, and merge concepts.")
        
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            help="Supports multi-page PDF documents and standard UTF-8 text notes.",
            label_visibility="collapsed"
        )

        if uploaded_files:
            if st.button("🚀 Extract Knowledge & Build Graph", type="primary", use_container_width=True):
                if not st.session_state.api_key:
                    st.error("Please enter a valid API Key in the sidebar.")
                elif not st.session_state.db_connected:
                    st.error("Neo4j database is disconnected.")
                else:
                    prog_bar = st.progress(0)
                    status_banner = st.empty()

                    for idx, file in enumerate(uploaded_files):
                        status_banner.info(f"Extracting concepts from '{file.name}' using **{st.session_state.model_choice}**...")
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
                                st.warning(f"⚠️ {result['message']}")
                            else:
                                st.success(f"✅ {result['message']} (Extracted {result['concepts_extracted']} concepts, {result['relationships_extracted']} relationships)")
                        except Exception as err:
                            st.error(f"❌ Extraction error on '{file.name}': {str(err)}")
                        
                        prog_bar.progress((idx + 1) / len(uploaded_files))
                    
                    status_banner.success("All documents processed successfully!")
                    time.sleep(1)
                    st.rerun()

    with col_up2:
        st.markdown('<div class="workspace-card-title">Supported Formats & Pipeline</div>', unsafe_allow_html=True)
        st.markdown("""
        - **PDF Documents** (`.pdf`): PyMuPDF multi-page extraction with page tracking.
        - **Text Notes** (`.txt`): UTF-8 structured text processing.
        - **Deduplication Engine**: Automatic concept normalization & alias resolution.
        - **Source Attribution**: Retains exact document and page references for every node.
        """)

    st.markdown("---")
    st.markdown('<div class="workspace-card-title">Indexed Document Registry</div>', unsafe_allow_html=True)
    st.caption("Manage existing knowledge base documents. Reprocess to refresh concepts or delete to remove.")

    if st.session_state.db_connected:
        docs = db.get_all_documents()
        if docs:
            for d in docs:
                col_info, col_acts = st.columns([3, 1.2])
                with col_info:
                    st.markdown(f"""
                    <div class="doc-row">
                        <div class="doc-info">
                            <div class="doc-icon">{'PDF' if d['doc_name'].endswith('.pdf') else 'TXT'}</div>
                            <div>
                                <div class="doc-name">{d['doc_name']}</div>
                                <div class="doc-meta">Pages: <strong>{d['page_count']}</strong> &nbsp;|&nbsp; Extracted Concepts: <strong>{d['concept_count']}</strong> &nbsp;|&nbsp; Added: {d['created_at'][:10]}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_acts:
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🔄 Reprocess", key=f"reproc_{d['doc_name']}", use_container_width=True):
                            st.info(f"To reprocess, re-upload '{d['doc_name']}' above.")
                    with col_b2:
                        if st.button("🗑️ Delete", key=f"del_{d['doc_name']}", use_container_width=True):
                            db.delete_document(d['doc_name'])
                            st.success(f"Deleted '{d['doc_name']}' and its exclusive graph nodes.")
                            time.sleep(0.8)
                            st.rerun()
        else:
            st.info("No documents currently stored in the knowledge graph. Upload documents above to begin.")

# ----------------------------------------------------
# TAB 3: GROUNDED QUESTION ANSWERING ASSISTANT
# ----------------------------------------------------
with tab_qa:
    st.markdown("""
    <div class="qa-banner">
        <span>🛡️</span>
        <span><strong>Grounded GraphRAG Engine:</strong> Responses are synthesized strictly from connected graph concepts and verifiable document source text.</span>
    </div>
    """, unsafe_allow_html=True)

    # Preset Sample Questions Bar
    st.markdown("**Suggested Research Questions:**")
    preset_cols = st.columns(3)
    preset_q = None
    with preset_cols[0]:
        if st.button("What concepts are connected to Machine Learning?", use_container_width=True):
            preset_q = "What concepts are connected to Machine Learning?"
    with preset_cols[1]:
        if st.button("Explain Gradient Descent & Backpropagation", use_container_width=True):
            preset_q = "Explain the relationship between Gradient Descent and Backpropagation."
    with preset_cols[2]:
        if st.button("Summarize key concepts in my notes", use_container_width=True):
            preset_q = "Summarize the primary topics and relationships in my uploaded notes."

    # Render Conversation History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                st.markdown("**📍 Verified Sources Cited:**")
                for cite in msg["citations"]:
                    st.markdown(f'<span class="citation-tag">📍 {cite["citation"]} ({cite["concept"]})</span>', unsafe_allow_html=True)

    # Prompt Input Bar
    user_input = st.chat_input("Ask a question about your knowledge graph...")
    query_to_process = preset_q or user_input

    if query_to_process:
        if not st.session_state.api_key:
            st.error("Please enter your API Key in the sidebar.")
        elif not st.session_state.db_connected:
            st.error("Neo4j database is disconnected.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Traversing Knowledge Graph & generating grounded synthesis..."):
                    answer, citations = QAEngine.answer_question(
                        user_question=query_to_process,
                        db=db,
                        api_key=st.session_state.api_key,
                        model_name=st.session_state.model_choice
                    )
                    st.markdown(answer)
                    if citations:
                        st.markdown("**📍 Verified Sources Cited:**")
                        for cite in citations:
                            st.markdown(f'<span class="citation-tag">📍 {cite["citation"]} ({cite["concept"]})</span>', unsafe_allow_html=True)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })
