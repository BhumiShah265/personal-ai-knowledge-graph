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

# Streamlit Page Configuration
st.set_page_config(
    page_title="Personal AI Knowledge Graph",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Editorial & Workspace Styling
STYLING_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Warm Ivory / Neutral Background */
    .stApp {
        background-color: #FAFAF9;
        color: #18181B;
    }

    /* Clean Page Header */
    .page-header {
        margin-bottom: 22px;
        padding-bottom: 14px;
        border-bottom: 1px solid #E4E4E7;
    }

    .page-title {
        font-size: 24px;
        font-weight: 700;
        color: #18181B;
        letter-spacing: -0.5px;
        margin: 0;
    }

    .page-subtitle {
        font-size: 13.5px;
        color: #71717A;
        margin-top: 4px;
    }

    .page-summary-strip {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 12.5px;
        color: #71717A;
        margin-top: 8px;
    }

    .page-summary-strip strong {
        color: #18181B;
    }

    /* Navigation Styling in Sidebar */
    .sidebar-brand {
        padding: 6px 0 16px 0;
        margin-bottom: 12px;
        border-bottom: 1px solid #E4E4E7;
    }

    .brand-title {
        font-size: 16px;
        font-weight: 800;
        color: #18181B;
        letter-spacing: -0.3px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .brand-desc {
        font-size: 11.5px;
        color: #71717A;
        margin-top: 2px;
    }

    /* Database Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11.5px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
    }

    .status-badge.connected {
        background: #F0FDF4;
        color: #166534;
        border: 1px solid #BBF7D0;
    }

    .status-badge.disconnected {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }

    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }

    .status-dot.connected {
        background: #22C55E;
    }

    .status-dot.disconnected {
        background: #EF4444;
    }

    /* Graph Legend Chips */
    .legend-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        align-items: center;
        padding: 8px 12px;
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 8px;
        margin-bottom: 12px;
    }

    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        font-weight: 600;
        color: #3F3F46;
        padding: 2px 7px;
        background: #F4F4F5;
        border-radius: 4px;
    }

    .legend-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
    }

    /* Concept Inspector Panel */
    .inspector-panel {
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(24, 24, 27, 0.03);
    }

    .inspector-name {
        font-size: 17px;
        font-weight: 700;
        color: #18181B;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .inspector-type {
        display: inline-block;
        background: #F5F3FF;
        color: #7C3AED;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    .inspector-desc {
        font-size: 13px;
        line-height: 1.55;
        color: #3F3F46;
        background: #FAFAF9;
        border: 1px solid #F4F4F5;
        border-radius: 6px;
        padding: 10px 12px;
        margin: 10px 0;
    }

    .citation-pill {
        display: inline-flex;
        align-items: center;
        background: #F4F4F5;
        color: #3F3F46;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 7px;
        border-radius: 4px;
        border: 1px solid #E4E4E7;
        margin-right: 5px;
        margin-bottom: 5px;
    }

    .rel-row {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #3F3F46;
        padding: 4px 8px;
        background: #FAFAF9;
        border-radius: 4px;
        margin-bottom: 4px;
        border: 1px solid #F4F4F5;
    }

    .rel-tag {
        font-size: 10px;
        font-weight: 700;
        color: #7C3AED;
        background: #F5F3FF;
        padding: 1px 5px;
        border-radius: 3px;
        text-transform: uppercase;
    }

    /* Document Library Table */
    .doc-table-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 14px;
        background: #F4F4F5;
        border-radius: 6px;
        font-size: 11.5px;
        font-weight: 700;
        color: #71717A;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }

    .doc-table-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        transition: border-color 0.15s ease;
    }

    .doc-table-row:hover {
        border-color: #CBD5E1;
    }

    .doc-file-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .doc-ext-badge {
        font-size: 10.5px;
        font-weight: 700;
        background: #F5F3FF;
        color: #7C3AED;
        padding: 3px 6px;
        border-radius: 4px;
    }

    .doc-title {
        font-size: 13.5px;
        font-weight: 600;
        color: #18181B;
    }

    .doc-stats {
        font-size: 12px;
        color: #71717A;
        margin-top: 2px;
    }

    /* Q&A Assistant Section */
    .qa-grounded-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 600;
        color: #6D28D9;
        background: #F5F3FF;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #DDD6FE;
        margin-bottom: 14px;
    }

    .qa-response-box {
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-left: 3.5px solid #7C3AED;
        border-radius: 8px;
        padding: 16px 18px;
        margin: 12px 0;
        font-size: 13.5px;
        line-height: 1.6;
        color: #18181B;
    }

    .qa-sources-box {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #F4F4F5;
        font-size: 12px;
        color: #71717A;
    }

    /* Empty State Container */
    .empty-box {
        text-align: center;
        padding: 42px 20px;
        background: #FFFFFF;
        border: 1px dashed #D4D4D8;
        border-radius: 10px;
        margin: 20px 0;
    }

    .empty-box-title {
        font-size: 15px;
        font-weight: 700;
        color: #27272A;
        margin: 8px 0 4px 0;
    }

    .empty-box-sub {
        font-size: 12.5px;
        color: #71717A;
        max-width: 420px;
        margin: 0 auto;
    }

    /* Primary Buttons */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        padding: 5px 14px;
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
if "file_cache" not in st.session_state:
    st.session_state.file_cache = {}

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
# PRODUCT NAVIGATION SIDEBAR
# ----------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-title">🧠 Personal Knowledge Graph</div>
        <div class="brand-desc">Research Intelligence & GraphRAG</div>
    </div>
    """, unsafe_allow_html=True)

    # Workspace Views Navigation
    active_nav = st.radio(
        "Workspace Navigation",
        ["Knowledge Graph", "Documents", "Ask Knowledge", "Settings & Sources"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Bottom Status Indicator
    if st.session_state.db_connected:
        st.markdown(
            '<div class="status-badge connected"><span class="status-dot connected"></span>Neo4j Connected</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-badge disconnected"><span class="status-dot disconnected"></span>Neo4j Offline</div>',
            unsafe_allow_html=True
        )

# Fetch current graph statistics
if st.session_state.db_connected:
    try:
        stats = db.get_graph_stats()
    except Exception:
        stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}
else:
    stats = {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}

# ----------------------------------------------------
# VIEW 1: KNOWLEDGE GRAPH (THE DOMINANT WORKSPACE)
# ----------------------------------------------------
if active_nav == "Knowledge Graph":
    st.markdown(f"""
    <div class="page-header">
        <h1 class="page-title">Knowledge Graph</h1>
        <div class="page-subtitle">Explore interconnected concepts and relationships across your document corpus</div>
        <div class="page-summary-strip">
            <span><strong>{stats["total_concepts"]}</strong> Concepts</span>
            <span>·</span>
            <span><strong>{stats["total_relationships"]}</strong> Relationships</span>
            <span>·</span>
            <span><strong>{stats["total_docs"]}</strong> Indexed Documents</span>
            <span>·</span>
            <span><strong>{stats["graph_density"]}</strong> Connections/Node</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.db_connected:
        st.markdown("""
        <div class="empty-box">
            <div style="font-size: 28px;">🔌</div>
            <div class="empty-box-title">Database Offline</div>
            <div class="empty-box-sub">Please connect your Neo4j instance in <strong>Settings & Sources</strong>.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Search & Filter Controls
        col_s1, col_s2, col_s3 = st.columns([2.5, 1.2, 1])
        with col_s1:
            search_query = st.text_input(
                "Search concepts", 
                placeholder="Filter graph by keyword, e.g. Neural Networks, Optimizer...", 
                label_visibility="collapsed"
            )
        with col_s2:
            all_types = db.get_all_entity_types()
            selected_type = st.selectbox("Filter Entity Type", all_types, label_visibility="collapsed")
        with col_s3:
            max_nodes = st.slider("Max Nodes", min_value=20, max_value=500, value=200, step=10, label_visibility="collapsed")

        # Entity Legend Bar
        legend_chips_html = "".join([
            f'<div class="legend-chip"><span class="legend-dot" style="background-color: {color};"></span>{etype}</div>'
            for etype, color in Config.ENTITY_COLORS.items() if etype != "DEFAULT"
        ])
        st.markdown(f'<div class="legend-bar"><span style="font-size: 11px; font-weight: 700; color: #71717A; margin-right: 4px;">ENTITY TYPES:</span>{legend_chips_html}</div>', unsafe_allow_html=True)

        graph_data = db.get_graph_data(search_query=search_query, entity_type_filter=selected_type, limit=max_nodes)
        
        if not graph_data["nodes"]:
            st.markdown("""
            <div class="empty-box">
                <div style="font-size: 32px;">🕸️</div>
                <div class="empty-box-title">No Knowledge Graph Data Found</div>
                <div class="empty-box-sub">Upload notes in <strong>Documents</strong> or load sample study notes in <strong>Settings & Sources</strong>.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            col_graph, col_inspector = st.columns([2.9, 1.1])
            
            with col_graph:
                st.caption(f"Displaying **{len(graph_data['nodes'])}** nodes & **{len(graph_data['edges'])}** relationships. Drag to arrange, scroll to zoom, click any node to inspect.")
                html_code = GraphVisualizer.generate_html(graph_data, height="750px")
                components.html(html_code, height=770, scrolling=False)

            with col_inspector:
                st.markdown('<div class="inspector-name"><span>Concept Inspector</span></div>', unsafe_allow_html=True)
                st.caption("Select a concept to inspect description, provenance, and relationships.")
                
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
                        <div class="inspector-panel">
                            <div class="inspector-name">
                                <span>{details['name']}</span>
                                <span class="inspector-type" style="color: {type_color};">{details['entity_type']}</span>
                            </div>
                            <div class="inspector-desc">{details['description']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("**Provenance & Sources**")
                        for doc in details['source_docs']:
                            st.markdown(f"- 📄 `{doc}`")
                        
                        st.markdown("**Page Citations**")
                        cites_html = "".join([f'<span class="citation-pill">📍 {p}</span>' for p in details['source_pages']])
                        st.markdown(cites_html, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("**Connected Knowledge**")
                        if details['outgoing_relationships']:
                            for rel in details['outgoing_relationships']:
                                st.markdown(f"""
                                <div class="rel-row">
                                    <span>➔</span>
                                    <span class="rel-tag">{rel['type']}</span>
                                    <strong>{rel['target']}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                        if details['incoming_relationships']:
                            for rel in details['incoming_relationships']:
                                st.markdown(f"""
                                <div class="rel-row">
                                    <span>⬅</span>
                                    <span class="rel-tag">{rel['type']}</span>
                                    <strong>{rel['source']}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.info("💡 Select any concept from the dropdown or click a node on the canvas to inspect its details.")

# ----------------------------------------------------
# VIEW 2: DOCUMENTS (DOCUMENT LIBRARY)
# ----------------------------------------------------
elif active_nav == "Documents":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Documents</h1>
        <div class="page-subtitle">Manage the source files behind your knowledge graph</div>
    </div>
    """, unsafe_allow_html=True)

    col_up1, col_up2 = st.columns([1.6, 1])
    with col_up1:
        st.markdown("**Upload Source Notes**")
        st.caption("Upload multi-page PDFs or UTF-8 text notes for entity extraction and concept merging.")
        
        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            help="Supports multi-page PDF documents and standard text notes.",
            label_visibility="collapsed"
        )

        if uploaded_files:
            if st.button("🚀 Extract & Index Documents", type="primary", use_container_width=True):
                if not st.session_state.api_key:
                    st.error("Please enter an API Key in Settings & Sources.")
                elif not st.session_state.db_connected:
                    st.error("Neo4j database is offline.")
                else:
                    prog_bar = st.progress(0)
                    status_banner = st.empty()

                    for idx, file in enumerate(uploaded_files):
                        status_banner.info(f"Extracting concepts from '{file.name}' using {st.session_state.model_choice}...")
                        try:
                            file_bytes = file.read()
                            st.session_state.file_cache[file.name] = file_bytes
                            
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
                    
                    status_banner.success("Document indexing complete!")
                    time.sleep(1)
                    st.rerun()

    with col_up2:
        st.markdown("**Pipeline Capabilities**")
        st.markdown("""
        - **PyMuPDF Parser**: Multi-page PDF parsing with page-level provenance.
        - **Intelligent Deduplication**: Canonical name normalization and alias merging.
        - **Persistent Graph Storage**: Source attribution stored directly on Neo4j relationships.
        """)

    st.markdown("---")
    st.markdown("### Indexed Document Library")
    
    if st.session_state.db_connected:
        docs = db.get_all_documents()
        if docs:
            for d in docs:
                col_d_info, col_d_actions = st.columns([3, 1.2])
                with col_d_info:
                    doc_ext = "PDF" if d['doc_name'].endswith('.pdf') else "TXT"
                    st.markdown(f"""
                    <div class="doc-table-row">
                        <div class="doc-file-info">
                            <span class="doc-ext-badge">{doc_ext}</span>
                            <div>
                                <div class="doc-title">{d['doc_name']}</div>
                                <div class="doc-stats">Pages: <strong>{d['page_count']}</strong> &nbsp;|&nbsp; Concepts: <strong>{d['concept_count']}</strong> &nbsp;|&nbsp; Indexed: {d['created_at'][:10]}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_d_actions:
                    col_reproc, col_del = st.columns(2)
                    with col_reproc:
                        if st.button("🔄 Reprocess", key=f"reproc_{d['doc_name']}", use_container_width=True):
                            doc_bytes = st.session_state.file_cache.get(d['doc_name'])
                            if not doc_bytes and d['doc_name'] == "sample_ai_notes.txt":
                                sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_ai_notes.txt")
                                if os.path.exists(sample_path):
                                    with open(sample_path, "rb") as sf:
                                        doc_bytes = sf.read()

                            if doc_bytes:
                                if not st.session_state.api_key:
                                    st.error("Please enter an API Key in Settings.")
                                else:
                                    with st.spinner(f"Reprocessing '{d['doc_name']}'..."):
                                        res = DocumentManager.process_document(
                                            file_name=d['doc_name'],
                                            file_bytes=doc_bytes,
                                            db=db,
                                            api_key=st.session_state.api_key,
                                            model_name=st.session_state.model_choice,
                                            force_reprocess=True
                                        )
                                        st.success(f"Reprocessed '{d['doc_name']}'! Extracted {res['concepts_extracted']} concepts.")
                                        time.sleep(1)
                                        st.rerun()
                            else:
                                st.warning(f"Please re-upload '{d['doc_name']}' above to reprocess.")
                    
                    with col_del:
                        if st.button("🗑️ Delete", key=f"del_{d['doc_name']}", use_container_width=True):
                            db.delete_document(d['doc_name'])
                            if d['doc_name'] in st.session_state.file_cache:
                                del st.session_state.file_cache[d['doc_name']]
                            st.success(f"Deleted '{d['doc_name']}' and its exclusive graph nodes.")
                            time.sleep(0.8)
                            st.rerun()
        else:
            st.markdown("""
            <div class="empty-box">
                <div style="font-size: 28px;">📄</div>
                <div class="empty-box-title">No Documents in Library</div>
                <div class="empty-box-sub">Upload PDF or TXT files above to populate your knowledge base.</div>
            </div>
            """, unsafe_allow_html=True)

# ----------------------------------------------------
# VIEW 3: ASK KNOWLEDGE (GROUNDED RESEARCH ASSISTANT)
# ----------------------------------------------------
elif active_nav == "Ask Knowledge":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Ask Knowledge</h1>
        <div class="page-subtitle">Synthesize answers strictly grounded in your uploaded documents with verifiable citations</div>
    </div>
    """, unsafe_allow_html=True)

    col_qa_head, col_qa_reset = st.columns([3, 1])
    with col_qa_head:
        st.markdown('<div class="qa-grounded-badge">🛡️ Grounded GraphRAG: Responses cite exact document pages</div>', unsafe_allow_html=True)
    with col_qa_reset:
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    # Preset Research Prompts
    st.markdown("**Suggested Research Queries:**")
    preset_cols = st.columns(3)
    preset_q = None
    with preset_cols[0]:
        if st.button("What concepts connect to Machine Learning?", use_container_width=True):
            preset_q = "What concepts are connected to Machine Learning?"
    with preset_cols[1]:
        if st.button("Explain Gradient Descent & Backpropagation", use_container_width=True):
            preset_q = "Explain the relationship between Gradient Descent and Backpropagation."
    with preset_cols[2]:
        if st.button("Summarize key topics in my notes", use_container_width=True):
            preset_q = "Summarize the primary topics and relationships in my uploaded notes."

    # Conversation History Render
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty-box">
            <div style="font-size: 30px;">💬</div>
            <div class="empty-box-title">Grounded Research Assistant</div>
            <div class="empty-box-sub">Ask any question across your knowledge corpus. Every synthesized claim references its source document and page number.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    st.markdown(f'<div class="qa-response-box">{msg["content"]}</div>', unsafe_allow_html=True)
                    if "citations" in msg and msg["citations"]:
                        st.markdown("<div class='qa-sources-box'><strong>Verified Sources Cited:</strong><br>", unsafe_allow_html=True)
                        for cite in msg["citations"]:
                            st.markdown(f'<span class="citation-pill">📍 {cite["citation"]} ({cite["concept"]})</span>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown(msg["content"])

    # Prompt Input Bar
    user_input = st.chat_input("Ask a question about your knowledge graph...")
    query_to_process = preset_q or user_input

    if query_to_process:
        if not st.session_state.api_key:
            st.error("Please enter your API Key in Settings & Sources.")
        elif not st.session_state.db_connected:
            st.error("Neo4j database is disconnected.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": query_to_process})
            with st.chat_message("user"):
                st.markdown(query_to_process)

            with st.chat_message("assistant"):
                with st.spinner("Searching graph & synthesizing grounded answer..."):
                    answer, citations = QAEngine.answer_question(
                        user_question=query_to_process,
                        db=db,
                        api_key=st.session_state.api_key,
                        model_name=st.session_state.model_choice
                    )
                    st.markdown(f'<div class="qa-response-box">{answer}</div>', unsafe_allow_html=True)
                    if citations:
                        st.markdown("<div class='qa-sources-box'><strong>Verified Sources Cited:</strong><br>", unsafe_allow_html=True)
                        for cite in citations:
                            st.markdown(f'<span class="citation-pill">📍 {cite["citation"]} ({cite["concept"]})</span>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })

# ----------------------------------------------------
# VIEW 4: SETTINGS & SOURCES
# ----------------------------------------------------
elif active_nav == "Settings & Sources":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Settings & Configuration</h1>
        <div class="page-subtitle">Configure AI model providers, Neo4j database credentials, and manage datasets</div>
    </div>
    """, unsafe_allow_html=True)

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.markdown("### 🤖 AI Model Provider")
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

    with col_set2:
        st.markdown("### 🔌 Neo4j Database")
        neo_uri = st.text_input("Bolt URI", value=Config.NEO4J_URI)
        neo_user = st.text_input("Username", value=Config.NEO4J_USERNAME)
        neo_pass = st.text_input("Password", value=Config.NEO4J_PASSWORD, type="password")
        if st.button("Test & Save Connection", use_container_width=True):
            db.uri = neo_uri
            db.username = neo_user
            db.password = neo_pass
            test_and_connect_db()
            if st.session_state.db_connected:
                st.success("Connected to Neo4j successfully!")
            else:
                st.error("Failed to connect to Neo4j.")
            st.rerun()

    st.markdown("---")
    col_demo, col_danger = st.columns(2)
    
    with col_demo:
        st.markdown("### 📥 Demo Dataset")
        st.caption("Quickly populate the knowledge graph with pre-packaged Machine Learning and Robotics study notes.")
        if st.button("Load Sample Study Notes", type="primary", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Please enter an API Key first.")
            elif not st.session_state.db_connected:
                st.error("Neo4j database is offline.")
            else:
                with st.spinner(f"Ingesting sample notes using {st.session_state.model_choice}..."):
                    try:
                        sample_txt_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_ai_notes.txt")
                        if os.path.exists(sample_txt_path):
                            with open(sample_txt_path, "rb") as f:
                                content = f.read()
                            st.session_state.file_cache["sample_ai_notes.txt"] = content
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

    with col_danger:
        st.markdown("### 🚨 Danger Zone")
        st.caption("Permanently delete all nodes, relationships, and document references from Neo4j.")
        confirm_check = st.checkbox("I confirm permanent purge of knowledge graph", key="danger_wipe_check")
        if st.button("Clear Knowledge Graph", disabled=not confirm_check, use_container_width=True):
            if st.session_state.db_connected:
                db.reset_graph()
                st.session_state.file_cache = {}
                st.session_state.chat_history = []
                st.success("Knowledge graph reset.")
                time.sleep(0.8)
                st.rerun()
