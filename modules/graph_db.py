from neo4j import GraphDatabase, Driver
from typing import List, Dict, Any, Optional
import datetime
from config import Config

class GraphDatabaseConnector:
    """Persistent Neo4j Graph Database engine with intelligent concept deduplication and rich metadata."""

    def __init__(self, uri: str = None, username: str = None, password: str = None):
        self.uri = uri or Config.NEO4J_URI
        self.username = username or Config.NEO4J_USERNAME
        self.password = password or Config.NEO4J_PASSWORD
        self._driver: Optional[Driver] = None

    def connect(self) -> bool:
        """Establish connection to Neo4j and setup constraints."""
        try:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connectivity
            self._driver.verify_connectivity()
            self._init_schema()
            return True
        except Exception as e:
            self._driver = None
            raise ConnectionError(f"Failed to connect to Neo4j database at {self.uri}: {str(e)}")

    def close(self):
        """Close driver connection."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def _init_schema(self):
        """Initialize database uniqueness constraints and indexes."""
        queries = [
            "CREATE CONSTRAINT concept_norm_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.normalized_name IS UNIQUE",
            "CREATE CONSTRAINT doc_name_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_name IS UNIQUE",
            "CREATE INDEX concept_type_idx IF NOT EXISTS FOR (c:Concept) ON (c.entity_type)"
        ]
        with self._driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception:
                    pass

    def add_document_metadata(self, doc_name: str, file_hash: str, page_count: int) -> None:
        """Store or update document record in graph."""
        query = """
        MERGE (d:Document {doc_name: $doc_name})
        ON CREATE SET 
            d.file_hash = $file_hash,
            d.page_count = $page_count,
            d.created_at = $timestamp,
            d.status = 'PROCESSED'
        ON MATCH SET 
            d.file_hash = $file_hash,
            d.page_count = $page_count,
            d.updated_at = $timestamp,
            d.status = 'PROCESSED'
        """
        now = datetime.datetime.now().isoformat()
        with self._driver.session() as session:
            session.run(query, doc_name=doc_name, file_hash=file_hash, page_count=page_count, timestamp=now)

    def is_document_processed(self, file_hash: str) -> Optional[str]:
        """Check if document hash already exists in graph."""
        query = "MATCH (d:Document {file_hash: $file_hash}) RETURN d.doc_name AS doc_name LIMIT 1"
        with self._driver.session() as session:
            result = session.run(query, file_hash=file_hash)
            record = result.single()
            return record["doc_name"] if record else None

    def store_page_extraction(self, extraction_result: Dict[str, Any]) -> None:
        """
        Merge entities and relationships into Neo4j graph, deduplicating concept nodes
        and updating metadata (source documents, source pages, descriptions).
        """
        now = datetime.datetime.now().isoformat()
        entities = extraction_result.get("entities", [])
        relationships = extraction_result.get("relationships", [])

        with self._driver.session() as session:
            # 1. Merge Concept Nodes
            for entity in entities:
                page_citation = f"{entity['source_doc']}:P{entity['source_page']}"
                query = """
                MERGE (c:Concept {normalized_name: $normalized_name})
                ON CREATE SET 
                    c.name = $name,
                    c.entity_type = $entity_type,
                    c.description = $description,
                    c.source_docs = [$source_doc],
                    c.source_pages = [$page_citation],
                    c.created_at = $now,
                    c.updated_at = $now
                ON MATCH SET 
                    c.name = CASE WHEN size($name) > size(c.name) THEN $name ELSE c.name END,
                    c.entity_type = CASE WHEN c.entity_type = 'CONCEPT' OR c.entity_type = '' THEN $entity_type ELSE c.entity_type END,
                    c.source_docs = CASE WHEN NOT $source_doc IN c.source_docs THEN c.source_docs + [$source_doc] ELSE c.source_docs END,
                    c.source_pages = CASE WHEN NOT $page_citation IN c.source_pages THEN c.source_pages + [$page_citation] ELSE c.source_pages END,
                    c.description = CASE 
                        WHEN NOT c.description CONTAINS $description THEN c.description + ' | ' + $description 
                        ELSE c.description 
                    END,
                    c.updated_at = $now
                """
                session.run(
                    query,
                    normalized_name=entity["normalized_name"],
                    name=entity["name"],
                    entity_type=entity["entity_type"],
                    description=entity["description"],
                    source_doc=entity["source_doc"],
                    page_citation=page_citation,
                    now=now
                )

                # Link concept to document node
                link_doc_query = """
                MATCH (c:Concept {normalized_name: $normalized_name})
                MATCH (d:Document {doc_name: $source_doc})
                MERGE (c)-[:APPEARS_IN {page: $source_page}]->(d)
                """
                session.run(
                    link_doc_query,
                    normalized_name=entity["normalized_name"],
                    source_doc=entity["source_doc"],
                    source_page=entity["source_page"]
                )

            # 2. Merge Relationships between concepts
            for rel in relationships:
                rel_type = rel["relationship_type"]
                query = f"""
                MATCH (src:Concept {{normalized_name: $src_norm}})
                MATCH (tgt:Concept {{normalized_name: $tgt_norm}})
                MERGE (src)-[r:`{rel_type}`]->(tgt)
                ON CREATE SET 
                    r.description = $description,
                    r.confidence = $confidence,
                    r.source_doc = $source_doc,
                    r.source_page = $source_page,
                    r.created_at = $now
                ON MATCH SET 
                    r.description = CASE WHEN NOT r.description CONTAINS $description THEN r.description + ' | ' + $description ELSE r.description END,
                    r.source_doc = $source_doc,
                    r.source_page = $source_page,
                    r.updated_at = $now
                """
                session.run(
                    query,
                    src_norm=rel["source_norm"],
                    tgt_norm=rel["target_norm"],
                    description=rel["description"],
                    confidence=rel.get("confidence", 0.9),
                    source_doc=rel["source_doc"],
                    source_page=rel["source_page"],
                    now=now
                )

    def get_graph_data(self, search_query: str = "", entity_type_filter: str = "All", limit: int = 300) -> Dict[str, Any]:
        """Fetch nodes and edges for PyVis visualization rendering."""
        where_clauses = []
        params = {"limit": limit}

        if search_query.strip():
            where_clauses.append("(toLower(c.name) CONTAINS toLower($search) OR toLower(c.description) CONTAINS toLower($search))")
            params["search"] = search_query.strip()

        if entity_type_filter and entity_type_filter != "All":
            where_clauses.append("c.entity_type = $entity_type")
            params["entity_type"] = entity_type_filter

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        cypher_nodes = f"""
        MATCH (c:Concept)
        {where_str}
        RETURN c.normalized_name AS id, c.name AS label, c.entity_type AS type, 
               c.description AS description, c.source_docs AS source_docs, c.source_pages AS source_pages
        LIMIT $limit
        """

        nodes = []
        node_ids = set()

        with self._driver.session() as session:
            res_nodes = session.run(cypher_nodes, **params)
            for rec in res_nodes:
                node_id = rec["id"]
                node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": rec["label"],
                    "type": rec["type"] or "CONCEPT",
                    "description": rec["description"] or "",
                    "source_docs": rec["source_docs"] or [],
                    "source_pages": rec["source_pages"] or []
                })

            if not node_ids:
                return {"nodes": [], "edges": []}

            # Fetch edges connected to retrieved nodes
            cypher_edges = """
            MATCH (src:Concept)-[r]->(tgt:Concept)
            WHERE src.normalized_name IN $node_ids AND tgt.normalized_name IN $node_ids AND type(r) <> 'APPEARS_IN'
            RETURN src.normalized_name AS source, tgt.normalized_name AS target, 
                   type(r) AS rel_type, r.description AS description, r.source_doc AS source_doc, r.source_page AS source_page
            LIMIT 500
            """
            res_edges = session.run(cypher_edges, node_ids=list(node_ids))
            edges = []
            for rec in res_edges:
                edges.append({
                    "source": rec["source"],
                    "target": rec["target"],
                    "type": rec["rel_type"],
                    "description": rec["description"] or "",
                    "source_doc": rec["source_doc"] or "",
                    "source_page": rec["source_page"] or ""
                })

        return {"nodes": nodes, "edges": edges}

    def get_concept_details(self, normalized_name: str) -> Optional[Dict[str, Any]]:
        """Fetch rich details for a single concept node, including connections and source notes."""
        cypher = """
        MATCH (c:Concept {normalized_name: $norm_name})
        OPTIONAL MATCH (c)-[r]->(tgt:Concept) WHERE type(r) <> 'APPEARS_IN'
        OPTIONAL MATCH (src:Concept)-[r_in]->(c) WHERE type(r_in) <> 'APPEARS_IN'
        RETURN c, 
               collect(DISTINCT {target: tgt.name, type: type(r), desc: r.description}) AS outgoing,
               collect(DISTINCT {source: src.name, type: type(r_in), desc: r_in.description}) AS incoming
        """
        with self._driver.session() as session:
            res = session.run(cypher, norm_name=normalized_name)
            rec = res.single()
            if not rec or not rec["c"]:
                return None

            c = rec["c"]
            return {
                "name": c.get("name"),
                "normalized_name": c.get("normalized_name"),
                "entity_type": c.get("entity_type", "CONCEPT"),
                "description": c.get("description", ""),
                "source_docs": c.get("source_docs", []),
                "source_pages": c.get("source_pages", []),
                "created_at": c.get("created_at", ""),
                "updated_at": c.get("updated_at", ""),
                "outgoing_relationships": [rel for rel in rec["outgoing"] if rel["target"]],
                "incoming_relationships": [rel for rel in rec["incoming"] if rel["source"]]
            }

    def get_graph_stats(self) -> Dict[str, Any]:
        """Compute summary metrics for dashboard display."""
        cypher = """
        MATCH (c:Concept) WITH count(c) AS total_concepts
        MATCH (d:Document) WITH total_concepts, count(d) AS total_docs
        MATCH ()-[r]->() WHERE type(r) <> 'APPEARS_IN' WITH total_concepts, total_docs, count(r) AS total_rels
        RETURN total_concepts, total_docs, total_rels
        """
        with self._driver.session() as session:
            res = session.run(cypher)
            rec = res.single()
            if rec:
                concepts = rec["total_concepts"]
                docs = rec["total_docs"]
                rels = rec["total_rels"]
                density = round(rels / max(concepts, 1), 2)
                return {
                    "total_concepts": concepts,
                    "total_docs": docs,
                    "total_relationships": rels,
                    "graph_density": density
                }
            return {"total_concepts": 0, "total_docs": 0, "total_relationships": 0, "graph_density": 0.0}

    def get_all_entity_types(self) -> List[str]:
        """Fetch list of distinct entity types present in the graph."""
        cypher = "MATCH (c:Concept) RETURN DISTINCT c.entity_type AS type ORDER BY type"
        with self._driver.session() as session:
            res = session.run(cypher)
            types = [rec["type"] for rec in res if rec["type"]]
            return ["All"] + types

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Fetch list of uploaded documents and their statistics."""
        cypher = """
        MATCH (d:Document)
        OPTIONAL MATCH (c:Concept)-[:APPEARS_IN]->(d)
        RETURN d.doc_name AS doc_name, d.page_count AS page_count, d.created_at AS created_at,
               count(DISTINCT c) AS concept_count
        ORDER BY created_at DESC
        """
        with self._driver.session() as session:
            res = session.run(cypher)
            docs = []
            for rec in res:
                docs.append({
                    "doc_name": rec["doc_name"],
                    "page_count": rec["page_count"] or 1,
                    "created_at": rec["created_at"] or "N/A",
                    "concept_count": rec["concept_count"] or 0
                })
            return docs

    def delete_document(self, doc_name: str) -> None:
        """Delete a document and detach concepts that only appear in this document."""
        cypher = """
        MATCH (d:Document {doc_name: $doc_name})
        OPTIONAL MATCH (c:Concept)-[:APPEARS_IN]->(d)
        DETACH DELETE d
        WITH c WHERE c IS NOT NULL AND size(c.source_docs) <= 1
        DETACH DELETE c
        """
        with self._driver.session() as session:
            session.run(cypher, doc_name=doc_name)

    def reset_graph(self) -> None:
        """Completely wipe the Neo4j database."""
        cypher = "MATCH (n) DETACH DELETE n"
        with self._driver.session() as session:
            session.run(cypher)
