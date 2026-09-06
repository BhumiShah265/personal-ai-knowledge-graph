import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

class ExtractedEntity(BaseModel):
    name: str = Field(description="Name of the concept/entity in original format")
    entity_type: str = Field(description="Type of entity, e.g., CONCEPT, TECHNOLOGY, METHOD, THEORY, PERSON, ORGANIZATION, METRIC, ALGORITHM")
    description: str = Field(description="Clear, concise 1-2 sentence description of this entity based on the document")

class ExtractedRelationship(BaseModel):
    source_entity: str = Field(description="Exact name of the source entity")
    relationship_type: str = Field(description="Uppercase relationship verb/predicate, e.g. USES, IMPLEMENTS, DEPENDS_ON, OPTIMIZES, PART_OF, RELATED_TO")
    target_entity: str = Field(description="Exact name of the target entity")
    description: str = Field(description="Brief explanation of how source and target are related")
    confidence: float = Field(default=0.9, description="Confidence score from 0.0 to 1.0")

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity]
    relationships: List[ExtractedRelationship]

class AIExtractor:
    """AI Entity and Relationship Extraction Engine supporting both OpenAI and Groq APIs."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize entity name for intelligent deduplication (lowercase, stripped, single spaces)."""
        clean = re.sub(r'[^\w\s]', '', name.strip().lower())
        return re.sub(r'\s+', ' ', clean)

    @classmethod
    def get_client(cls, api_key: str) -> OpenAI:
        """Return configured OpenAI/Groq client based on API key prefix."""
        if api_key.startswith("gsk_"):
            return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        return OpenAI(api_key=api_key)

    @classmethod
    def extract_knowledge(
        cls, 
        page_content: Dict[str, Any], 
        api_key: str, 
        model_name: str = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Process a single document page and return structured entities and relationships.
        """
        if not api_key:
            raise ValueError("API key is missing. Please set your OpenAI or Groq API key.")

        client = cls.get_client(api_key)
        doc_name = page_content["doc_name"]
        page_num = page_content["page_num"]
        text = page_content["text"]

        prompt = f"""
You are an expert AI knowledge graph engineer. Analyze the following document text from Document "{doc_name}", Page {page_num}.

Extract key domain concepts, technologies, methods, theories, metrics, algorithms, people, and organizations as ENTITIES.
For each entity, provide a concise 1-2 sentence summary.

Extract meaningful, directional RELATIONSHIPS between these entities (e.g. USES, IMPLEMENTS, DEPENDS_ON, OPTIMIZES, PART_OF, RELATED_TO).

---
TEXT CONTENT:
{text}
---

Return JSON in this EXACT structure:
{{
  "entities": [
    {{"name": "...", "entity_type": "...", "description": "..."}}
  ],
  "relationships": [
    {{"source_entity": "...", "relationship_type": "...", "target_entity": "...", "description": "...", "confidence": 0.9}}
  ]
}}
"""

        try:
            raw_entities = []
            raw_relationships = []

            # Determine parsing strategy based on key provider / model
            if api_key.startswith("sk-") and "gpt" in model_name.lower():
                try:
                    response = client.beta.chat.completions.parse(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You extract structured knowledge graphs from text strictly following the output format."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format=ExtractionResult,
                        temperature=0.0
                    )
                    parsed_data = response.choices[0].message.parsed
                    raw_entities = [item.model_dump() for item in parsed_data.entities]
                    raw_relationships = [item.model_dump() for item in parsed_data.relationships]
                except Exception:
                    # Fallback to json object mode
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You extract structured knowledge graphs. Output ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.0
                    )
                    data = json.loads(response.choices[0].message.content)
                    raw_entities = data.get("entities", [])
                    raw_relationships = data.get("relationships", [])
            else:
                # Groq / Generic OpenAI compatible mode
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You extract structured knowledge graphs from text. Output ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                data = json.loads(response.choices[0].message.content)
                raw_entities = data.get("entities", [])
                raw_relationships = data.get("relationships", [])

            # Enrich entities with normalization and metadata
            enriched_entities = []
            for item in raw_entities:
                name = str(item.get("name", "")).strip()
                norm_name = cls.normalize_name(name)
                if not norm_name:
                    continue
                
                enriched_entities.append({
                    "name": name,
                    "normalized_name": norm_name,
                    "entity_type": str(item.get("entity_type", "CONCEPT")).upper().strip(),
                    "description": str(item.get("description", "")).strip(),
                    "source_doc": doc_name,
                    "source_page": page_num
                })

            # Enrich relationships
            enriched_rels = []
            for rel in raw_relationships:
                src_name = str(rel.get("source_entity", "")).strip()
                tgt_name = str(rel.get("target_entity", "")).strip()
                src_norm = cls.normalize_name(src_name)
                tgt_norm = cls.normalize_name(tgt_name)

                if src_norm and tgt_norm and src_norm != tgt_norm:
                    rel_type = re.sub(r'[^A-Z0-9_]', '_', str(rel.get("relationship_type", "RELATED_TO")).upper().strip())
                    if not rel_type:
                        rel_type = "RELATED_TO"
                    
                    enriched_rels.append({
                        "source_entity": src_name,
                        "source_norm": src_norm,
                        "relationship_type": rel_type,
                        "target_entity": tgt_name,
                        "target_norm": tgt_norm,
                        "description": str(rel.get("description", "")).strip(),
                        "confidence": float(rel.get("confidence", 0.9)),
                        "source_doc": doc_name,
                        "source_page": page_num
                    })

            return {
                "entities": enriched_entities,
                "relationships": enriched_rels
            }

        except Exception as e:
            raise RuntimeError(f"AI Knowledge Extraction failed for page {page_num}: {str(e)}")
