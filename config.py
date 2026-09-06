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
    # Supports both OpenAI (sk-...) and Groq (gsk_...) keys
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

    # Graph Color Palette for Visualizer - Premium Purple-Accented Palette
    ENTITY_COLORS = {
        "CONCEPT": "#7C3AED",       # Primary Purple
        "TECHNOLOGY": "#2563EB",    # Deep Blue
        "METHOD": "#059669",        # Forest Emerald
        "THEORY": "#9333EA",        # Vivid Violet
        "PERSON": "#E11D48",        # Rose Crimson
        "ORGANIZATION": "#D97706",  # Warm Amber
        "METRIC": "#0891B2",        # Cyan Teal
        "ALGORITHM": "#4F46E5",     # Indigo
        "CATEGORY": "#6D28D9",      # Deep Purple
        "DEFAULT": "#64748B"        # Neutral Slate
    }

    # UI Theme Palette
    COLOR_PRIMARY = "#7C3AED"
    COLOR_PRIMARY_HOVER = "#6D28D9"
    COLOR_BG_WARM = "#F9F9FB"
    COLOR_SURFACE = "#FFFFFF"
    COLOR_TEXT_MAIN = "#0F172A"
    COLOR_TEXT_MUTED = "#64748B"
    COLOR_BORDER = "#E5E7EB"
