import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

class Config:
    # Neo4j Settings
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    # API Keys & Base URL Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or os.getenv("GROK_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    GROK_API_KEY = os.getenv("GROK_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

    # LLM Model Configuration
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    elif (OPENAI_API_KEY and OPENAI_API_KEY.startswith("gsk_")) or (GROK_API_KEY and GROK_API_KEY.startswith("gsk_")):
        LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    else:
        LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    # Limits
    MAX_FILE_SIZE_MB = 20
    SUPPORTED_EXTENSIONS = [".pdf", ".txt"]

    # Refined Editorial Palette for Knowledge Graph Entities
    ENTITY_COLORS = {
        "CONCEPT": "#7C3AED",       # Muted Violet / Primary
        "TECHNOLOGY": "#3B82F6",    # Slate Blue
        "METHOD": "#10B981",        # Muted Emerald
        "THEORY": "#8B5CF6",        # Lavender Purple
        "PERSON": "#F43F5E",        # Muted Rose
        "ORGANIZATION": "#F59E0B",  # Ochre / Amber
        "METRIC": "#06B6D4",        # Soft Cyan
        "ALGORITHM": "#6366F1",     # Indigo
        "CATEGORY": "#A855F7",      # Purple
        "DEFAULT": "#64748B"        # Neutral Slate
    }

    # UI Theme Palette - Warm Editorial Minimal
    COLOR_PRIMARY = "#7C3AED"
    COLOR_PRIMARY_HOVER = "#6D28D9"
    COLOR_BG = "#FAFAF9"
    COLOR_SURFACE = "#FFFFFF"
    COLOR_TEXT_MAIN = "#18181B"
    COLOR_TEXT_MUTED = "#71717A"
    COLOR_BORDER = "#E4E4E7"
