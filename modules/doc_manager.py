from typing import Dict, Any, List, Tuple
from modules.text_extractor import TextExtractor
from modules.ai_extractor import AIExtractor
from modules.graph_db import GraphDatabaseConnector

class DocumentManager:
    """Document Ingestion, Duplicate Detection, and Workflow Manager."""

    @classmethod
    def process_document(
        cls, 
        file_name: str, 
        file_bytes: bytes, 
        db: GraphDatabaseConnector, 
        api_key: str, 
        model_name: str = "gpt-4o-mini",
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text, prevent duplicates, process pages with LLM, and store graph in Neo4j.
        """
        # 1. Extract text and compute hash
        pages, file_hash = TextExtractor.extract_pages(file_name, file_bytes)

        # 2. Check for duplicates in Neo4j graph
        existing_doc_name = db.is_document_processed(file_hash)
        if existing_doc_name and not force_reprocess:
            return {
                "status": "DUPLICATE",
                "message": f"Document '{file_name}' has already been processed as '{existing_doc_name}'. Skipping duplicate extraction.",
                "doc_name": existing_doc_name,
                "pages_processed": 0,
                "concepts_added": 0
            }

        # If reprocessing existing doc, delete old nodes first
        if force_reprocess and existing_doc_name:
            db.delete_document(existing_doc_name)

        # 3. Store document metadata node
        db.add_document_metadata(file_name, file_hash, len(pages))

        # 4. Extract knowledge page by page
        total_entities = 0
        total_relationships = 0

        for page in pages:
            extraction_result = AIExtractor.extract_knowledge(
                page_content=page,
                api_key=api_key,
                model_name=model_name
            )
            # Store in Neo4j with deduplication
            db.store_page_extraction(extraction_result)

            total_entities += len(extraction_result.get("entities", []))
            total_relationships += len(extraction_result.get("relationships", []))

        return {
            "status": "SUCCESS",
            "message": f"Successfully processed '{file_name}' across {len(pages)} page(s).",
            "doc_name": file_name,
            "pages_processed": len(pages),
            "concepts_extracted": total_entities,
            "relationships_extracted": total_relationships
        }
