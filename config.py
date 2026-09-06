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
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

    # LLM Model Configuration
    LLM_MODEL = os.getenv("LLM_MODEL", "groq/compound-mini" if OPENAI_API_KEY.startswith("gsk_") else "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

    # Limits
    MAX_FILE_SIZE_MB = 20
    SUPPORTED_EXTENSIONS = [".pdf", ".txt"]

    # Graph Color Palette for Visualizer
    ENTITY_COLORS = {
        "CONCEPT": "#4F46E5",       # Indigo
        "TECHNOLOGY": "#0284C7",    # Sky Blue
        "METHOD": "#0D9488",        # Teal
        "THEORY": "#7C3AED",        # Purple
        "PERSON": "#E11D48",        # Rose
        "ORGANIZATION": "#D97706",  # Amber
        "METRIC": "#16A34A",        # Green
        "ALGORITHM": "#059669",     # Emerald
        "CATEGORY": "#8B5CF6",      # Violet
        "DEFAULT": "#64748B"        # Slate
    }

    # UI Theme Palette
    COLOR_PRIMARY = "#4F46E5"
    COLOR_BG_LIGHT = "#F8FAFC"
    COLOR_SURFACE = "#FFFFFF"
    COLOR_TEXT_MAIN = "#0F172A"
    COLOR_TEXT_MUTED = "#64748B"
    COLOR_BORDER = "#E2E8F0"
