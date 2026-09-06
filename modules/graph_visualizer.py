from pyvis.network import Network
import tempfile
import os
from typing import Dict, Any
from config import Config

class GraphVisualizer:
    """Renders interactive, zoomable, draggable HTML knowledge graphs using PyVis."""

    @classmethod
    def generate_html(cls, graph_data: Dict[str, Any], height: str = "650px") -> str:
        """
        Convert node and edge dictionary lists into a styled PyVis HTML graph visualization.
        """
        net = Network(
            height=height,
            width="100%",
            directed=True,
            bgcolor="#FAF8F5",
            font_color="#0F172A"
        )

        net.set_options("""
        {
          "nodes": {
            "font": {
              "size": 14,
              "face": "Inter, system-ui, sans-serif",
              "multi": "html"
            },
            "borderWidth": 2,
            "shadow": {
              "enabled": true,
              "color": "rgba(0,0,0,0.08)",
              "size": 6
            }
          },
          "edges": {
            "color": {
              "color": "#94A3B8",
              "highlight": "#4F46E5",
              "hover": "#4F46E5"
            },
            "font": {
              "size": 11,
              "align": "middle",
              "face": "Inter, system-ui, sans-serif"
            },
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 0.6 }
            },
            "smooth": {
              "type": "continuous",
              "roundness": 0.2
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragNodes": true,
            "dragView": true,
            "navigationButtons": true
          },
          "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "stabilization": { "iterations": 150 }
          }
        }
        """)

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Build node elements
        for n in nodes:
            entity_type = (n.get("type") or "CONCEPT").upper()
            color = Config.ENTITY_COLORS.get(entity_type, Config.ENTITY_COLORS["DEFAULT"])
            
            docs_list = ", ".join(n.get("source_docs", [])) or "None"
            pages_list = ", ".join(n.get("source_pages", [])) or "None"
            
            # Hover tooltip HTML format
            title_html = f"""
            <div style="font-family: system-ui; max-width: 280px; padding: 6px; font-size: 13px; line-height: 1.4;">
                <strong style="color: {color}; font-size: 14px;">{n['label']}</strong> 
                <span style="background: #EEF2FF; color: #4338CA; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">{entity_type}</span>
                <p style="margin: 6px 0; color: #334155;">{n.get('description', '')}</p>
                <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 4px 0;">
                <div style="color: #64748B; font-size: 11px;">
                    <strong>Sources:</strong> {docs_list}<br>
                    <strong>Citations:</strong> {pages_list}
                </div>
            </div>
            """

            net.add_node(
                n["id"],
                label=n["label"],
                title=title_html,
                color={
                    "background": "#FFFFFF",
                    "border": color,
                    "highlight": {"background": color, "border": color},
                    "hover": {"background": "#F1F5F9", "border": color}
                },
                shape="box",
                margin=10,
                group=entity_type
            )

        # Build edge elements
        for e in edges:
            rel_desc = e.get("description", "")
            doc_cite = f" ({e['source_doc']}:P{e['source_page']})" if e.get("source_doc") else ""
            edge_title = f"{e['type']}: {rel_desc}{doc_cite}" if rel_desc else f"{e['type']}{doc_cite}"
            
            net.add_edge(
                e["source"],
                e["target"],
                label=e["type"],
                title=edge_title
            )

        # Render HTML string
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            path = tmp_file.name

        net.save_graph(path)
        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Clean up temp file
        if os.path.exists(path):
            os.remove(path)

        return html_content
