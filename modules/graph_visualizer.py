from pyvis.network import Network
import tempfile
import os
from typing import Dict, Any
from config import Config

class GraphVisualizer:
    """Renders interactive, zoomable, draggable HTML knowledge graphs using PyVis."""

    @classmethod
    def generate_html(cls, graph_data: Dict[str, Any], height: str = "680px") -> str:
        """
        Convert node and edge dictionary lists into a styled PyVis HTML graph visualization.
        """
        net = Network(
            height=height,
            width="100%",
            directed=True,
            bgcolor="#F9F9FB",
            font_color="#0F172A"
        )

        net.set_options("""
        {
          "nodes": {
            "font": {
              "size": 13,
              "face": "Plus Jakarta Sans, Inter, system-ui, sans-serif",
              "color": "#0F172A",
              "multi": "html",
              "bold": {
                "color": "#0F172A"
              }
            },
            "borderWidth": 2,
            "borderWidthSelected": 3,
            "shapeProperties": {
              "borderRadius": 8
            },
            "shadow": {
              "enabled": true,
              "color": "rgba(15, 23, 42, 0.06)",
              "size": 8,
              "x": 0,
              "y": 2
            }
          },
          "edges": {
            "color": {
              "color": "#CBD5E1",
              "highlight": "#7C3AED",
              "hover": "#7C3AED"
            },
            "font": {
              "size": 11,
              "align": "middle",
              "face": "Plus Jakarta Sans, Inter, system-ui, sans-serif",
              "color": "#64748B",
              "strokeWidth": 2,
              "strokeColor": "#F9F9FB"
            },
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 0.5 }
            },
            "smooth": {
              "type": "cubicBezier",
              "forceDirection": "none",
              "roundness": 0.2
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 120,
            "zoomView": true,
            "dragNodes": true,
            "dragView": true,
            "navigationButtons": true,
            "keyboard": {
              "enabled": false
            }
          },
          "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -40,
              "centralGravity": 0.008,
              "springLength": 110,
              "springConstant": 0.08,
              "damping": 0.6
            },
            "maxVelocity": 45,
            "minVelocity": 0.1,
            "stabilization": { "iterations": 180 }
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
            <div style="font-family: 'Plus Jakarta Sans', system-ui, sans-serif; max-width: 290px; padding: 8px 10px; font-size: 12px; line-height: 1.45; background: #FFFFFF; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <strong style="color: #0F172A; font-size: 13px;">{n['label']}</strong>
                    <span style="background: #F3E8FF; color: {color}; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 700; text-transform: uppercase;">{entity_type}</span>
                </div>
                <p style="margin: 4px 0 8px 0; color: #475569; font-size: 12px;">{n.get('description', '')}</p>
                <div style="border-top: 1px solid #F1F5F9; padding-top: 6px; color: #64748B; font-size: 11px;">
                    <div><strong>Document:</strong> {docs_list}</div>
                    <div style="margin-top: 2px;"><strong>Citations:</strong> {pages_list}</div>
                </div>
            </div>
            """

            net.add_node(
                n["id"],
                label=f"<b>{n['label']}</b>",
                title=title_html,
                color={
                    "background": "#FFFFFF",
                    "border": color,
                    "highlight": {"background": "#F3E8FF", "border": color},
                    "hover": {"background": "#F8FAFC", "border": color}
                },
                shape="box",
                margin=9,
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
