# Personal AI Knowledge Graph

A production-grade interactive web application built with **Python**, **Streamlit**, **PyMuPDF**, **Neo4j**, **PyVis**, and **OpenAI**. Upload personal study notes, PDFs, or research documents to automatically extract domain concepts and relationships, construct a persistent deduplicated Neo4j Knowledge Graph, visually explore networks, and perform grounded Q&A with verifiable page-level citations.

---

## 🌟 Key Features

1. **Multi-Format Document Extraction**:
   - Parses both `.pdf` and `.txt` files with page-level text breakdown.
   - Powered by PyMuPDF (`pymupdf`) for fast, robust PDF parsing.
   - SHA-256 document fingerprinting to prevent duplicate document re-processing.

2. **AI Concept & Relationship Extraction**:
   - Structured LLM extraction identifying domain concepts, technologies, methods, theories, metrics, people, and organizations.
   - Automatic extraction of directional relationships (e.g. `USES`, `IMPLEMENTS`, `DEPENDS_ON`, `OPTIMIZES`, `PART_OF`).
   - Normalizes entity names to lowercased canonical forms for intelligent deduplication.

3. **Persistent Neo4j Graph Database**:
   - Intelligent concept deduplication: merging new document uploads with existing graph nodes without creating disconnected duplicate nodes.
   - Retains source document names and page numbers on every node and relationship.
   - Dynamic Cypher graph queries for stats, filtering, and detail inspection.

4. **Interactive Graph Visualization**:
   - Rendered using PyVis with smooth animations, zooming, panning, and draggable nodes.
   - Color-coded node types (Concept, Technology, Method, Theory, Person, Organization, Metric).
   - Rich hover tooltips displaying concept descriptions and source citations.

5. **Grounded GraphRAG Question Answering**:
   - Ask complex questions across your knowledge base (e.g., *"What concepts are connected to machine learning?"*, *"Explain the relationship between gradient descent and neural networks"*).
   - Grounded strictly in uploaded document context to prevent hallucinations.
   - Provides clear source citations with document names and page numbers.

6. **Polished User Interface**:
   - Modern light theme with Inter typography and responsive navigation tabs.
   - Document registry with concept stats, document deletion, and re-processing.
   - Danger zone for resetting/clearing the knowledge graph.
   - One-click **Demo Data Loader** for instant testing out-of-the-box.

---

## 🏗️ Project Architecture

```
personal-ai-knowledge-graph/
├── app.py                      # Main Streamlit UI application
├── config.py                   # Configuration and styling settings
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── README.md                   # Setup documentation
├── sample_data/                # Sample test documents
│   ├── sample_ai_notes.txt
│   └── sample_neural_nets.pdf
└── modules/
    ├── __init__.py
    ├── text_extractor.py       # PyMuPDF & TXT parser with page tracking
    ├── ai_extractor.py         # OpenAI structured extraction engine
    ├── graph_db.py             # Neo4j Cypher driver & deduplication engine
    ├── graph_visualizer.py     # PyVis HTML graph visualization builder
    ├── qa_engine.py            # Grounded GraphRAG QA with citations
    └── doc_manager.py          # Ingestion workflow & duplicate prevention
```

---

## ⚡ Quick Start & Setup Instructions

### 1. Prerequisites
- **Python 3.10+** installed.
- **Neo4j Instance** (Local Docker, Neo4j Desktop, or free Cloud Neo4j Aura).
- **OpenAI API Key** (for concept extraction and Q&A).

---

### 2. Neo4j Database Setup

#### Option A: Using Docker (Recommended & Quickest)
Run the following terminal command to start a local Neo4j container:
```bash
docker run \
    --name neo4j-knowledge-graph \
    -p 7687:7687 -p 7474:7474 \
    -d \
    --env NEO4J_AUTH=neo4j/password \
    neo4j:latest
```
- **Bolt URI**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: `password`
- **Browser Dashboard**: `http://localhost:7474`

#### Option B: Neo4j Desktop or Neo4j Aura (Cloud)
If using Neo4j Aura (Free Cloud Database) or Neo4j Desktop, note your Bolt URI (e.g. `neo4j+s://xxxx.databases.neo4j.io`), username, and password.

---

### 3. Installation

1. Clone or navigate to the project directory:
   ```bash
   cd /path/to/personal-ai-knowledge-graph
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### 4. Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your credentials:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=password
   OPENAI_API_KEY=your_actual_openai_api_key_here
   LLM_MODEL=gpt-4o-mini
   ```
   *(Note: You can also enter or update your OpenAI API key directly inside the Streamlit app sidebar).*

---

### 5. Running the Application

Launch the Streamlit web application:
```bash
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 How to Test with Sample Data

1. Open the application sidebar.
2. Ensure your OpenAI API Key is entered.
3. Click **"📥 Load Sample Documents"**.
4. The system will process `sample_ai_notes.txt` and `sample_neural_nets.pdf` into Neo4j.
5. Go to the **🔍 Graph Explorer** tab to interactively explore concepts like *Gradient Descent*, *Neural Networks*, *Transformers*, and *Robotics*.
6. Go to the **💬 Grounded Q&A Assistant** tab and click any example question to test grounded AI answers with page citations!
