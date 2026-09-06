from typing import List, Dict, Any, Tuple
from openai import OpenAI
from modules.graph_db import GraphDatabaseConnector
from modules.ai_extractor import AIExtractor
import re

class QAEngine:
    """Grounded Question Answering engine querying Neo4j knowledge graph supporting OpenAI & Groq."""

    @classmethod
    def answer_question(
        cls, 
        user_question: str, 
        db: GraphDatabaseConnector, 
        api_key: str, 
        model_name: str = "gpt-4o-mini"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant subgraph context from Neo4j and synthesize a grounded answer 
        with source citations.
        """
        if not api_key:
            raise ValueError("API key is missing. Please set your OpenAI or Groq API key.")

        # Extract search keywords from user question
        keywords = cls._extract_keywords(user_question)
        
        # Retrieve graph context from Neo4j
        context_str, citations = cls._retrieve_context(keywords, user_question, db)

        if not context_str.strip():
            return (
                "I couldn't find any relevant concepts or documents in your uploaded knowledge graph to answer this question.",
                []
            )

        client = AIExtractor.get_client(api_key)

        system_prompt = """
You are an AI Knowledge Graph Assistant. Your task is to answer user questions STRICTLY using the provided Knowledge Graph context and document excerpts.

STRICT GROUNDING RULES:
1. Base your answer ONLY on the provided context below. Do not use outside knowledge.
2. If the provided context does not contain sufficient facts to answer the question, state clearly: 
   "The uploaded documents do not contain enough information to answer this question."
3. Cite your sources clearly using standard citation tags like [Doc: filename, Page: X] or inline concept references.
4. Keep the answer structured, professional, clear, and informative.
"""

        user_prompt = f"""
QUESTION: {user_question}

EXTRACTED KNOWLEDGE GRAPH & DOCUMENT CONTEXT:
{context_str}

Please synthesize a complete, grounded answer with clear references to the source documents and page numbers.
"""

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )

            answer_text = response.choices[0].message.content.strip()
            return answer_text, citations

        except Exception as e:
            raise RuntimeError(f"Failed to generate QA response: {str(e)}")

    @staticmethod
    def _extract_keywords(question: str) -> List[str]:
        """Extract clean search terms from natural language question."""
        stop_words = {
            "what", "is", "are", "the", "how", "why", "which", "where", "who", 
            "explain", "relationship", "between", "connected", "to", "in", "my", 
            "notes", "documents", "uploaded", "summarize", "everything", "know", 
            "about", "does", "this", "concept", "main", "topics"
        }
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords or words

    @staticmethod
    def _retrieve_context(
        keywords: List[str], 
        question: str, 
        db: GraphDatabaseConnector
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Query Neo4j for matching concepts, relationships, and document sources."""
        if not db._driver:
            db.connect()

        concepts_found = []
        relationships_found = []
        citations_map = {}

        # Cypher query searching concepts by keyword
        cypher = """
        MATCH (c:Concept)
        WHERE ANY(kw IN $keywords WHERE toLower(c.name) CONTAINS kw OR toLower(c.description) CONTAINS kw)
        OPTIONAL MATCH (c)-[r]->(tgt:Concept) WHERE type(r) <> 'APPEARS_IN'
        RETURN c.name AS name, c.entity_type AS type, c.description AS desc, 
               c.source_docs AS docs, c.source_pages AS pages,
               collect(DISTINCT {target: tgt.name, rel: type(r), rel_desc: r.description}) AS rels
        LIMIT 15
        """

        with db._driver.session() as session:
            res = session.run(cypher, keywords=keywords)
            for rec in res:
                c_name = rec["name"]
                c_type = rec["type"]
                c_desc = rec["desc"]
                c_docs = rec["docs"] or []
                c_pages = rec["pages"] or []

                concepts_found.append(f"CONCEPT: {c_name} ({c_type})\nDescription: {c_desc}\nSources: {', '.join(c_pages)}")

                for cite in c_pages:
                    citations_map[cite] = {"concept": c_name, "citation": cite}

                for rel in rec["rels"]:
                    if rel["target"]:
                        rel_str = f"RELATIONSHIP: ({c_name}) --[{rel['rel']}]--> ({rel['target']})"
                        if rel["rel_desc"]:
                            rel_str += f" Details: {rel['rel_desc']}"
                        relationships_found.append(rel_str)

        # If no direct keyword match, grab top graph concepts to provide overview
        if not concepts_found:
            cypher_fallback = """
            MATCH (c:Concept)
            RETURN c.name AS name, c.entity_type AS type, c.description AS desc, c.source_pages AS pages
            LIMIT 10
            """
            with db._driver.session() as session:
                res = session.run(cypher_fallback)
                for rec in res:
                    concepts_found.append(f"CONCEPT: {rec['name']} ({rec['type']})\nDescription: {rec['desc']}")

        context_lines = []
        if concepts_found:
            context_lines.append("--- RELEVANT CONCEPTS ---")
            context_lines.extend(concepts_found)
        if relationships_found:
            context_lines.append("\n--- RELEVANT RELATIONSHIPS ---")
            context_lines.extend(relationships_found)

        citations_list = list(citations_map.values())
        return "\n\n".join(context_lines), citations_list
