from pyvis.network import Network
import tempfile
import os
import json
from typing import Dict, Any
from config import Config

class GraphVisualizer:
    """Renders high-grade interactive knowledge graphs using PyVis."""

    @classmethod
    def generate_html(cls, graph_data: Dict[str, Any], height: str = "750px") -> str:
        """
        Convert node and edge dictionary lists into a styled PyVis HTML graph visualization
        with rich interactive click-to-view definitions and clean formatted tooltips.
        """
        net = Network(
            height=height,
            width="100%",
            directed=True,
            bgcolor="#FAFAF9",
            font_color="#18181B"
        )

        net.set_options("""
        {
          "nodes": {
            "font": {
              "size": 13,
              "face": "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, sans-serif",
              "color": "#18181B",
              "multi": "html",
              "bold": {
                "color": "#18181B"
              }
            },
            "borderWidth": 1.5,
            "borderWidthSelected": 2.5,
            "shapeProperties": {
              "borderRadius": 6
            },
            "shadow": {
              "enabled": true,
              "color": "rgba(24, 24, 27, 0.06)",
              "size": 6,
              "x": 0,
              "y": 2
            }
          },
          "edges": {
            "color": {
              "color": "#CBD5E1",
              "highlight": "#7C3AED",
              "hover": "#7C3AED",
              "opacity": 0.85
            },
            "font": {
              "size": 10,
              "align": "middle",
              "face": "Plus Jakarta Sans, sans-serif",
              "color": "#71717A",
              "strokeWidth": 2,
              "strokeColor": "#FAFAF9"
            },
            "arrows": {
              "to": { "enabled": true, "scaleFactor": 0.45 }
            },
            "smooth": {
              "type": "cubicBezier",
              "forceDirection": "none",
              "roundness": 0.2
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 90,
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
              "gravitationalConstant": -45,
              "centralGravity": 0.007,
              "springLength": 125,
              "springConstant": 0.08,
              "damping": 0.7
            },
            "maxVelocity": 40,
            "minVelocity": 0.1,
            "stabilization": { "iterations": 180 }
          }
        }
        """)

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Build lookup for click inspector overlay
        nodes_metadata = {}

        # Build node elements
        for n in nodes:
            entity_type = (n.get("type") or "CONCEPT").upper()
            color = Config.ENTITY_COLORS.get(entity_type, Config.ENTITY_COLORS["DEFAULT"])
            
            docs_list = ", ".join(n.get("source_docs", [])) or "None"
            pages_list = ", ".join(n.get("source_pages", [])) or "None"
            desc = n.get("description", "No description available").strip()
            
            # Clean plain-text tooltip (No raw HTML tags)
            clean_tooltip = f"{n['label']} [{entity_type}]\n\n{desc}\n\nSources: {docs_list}\nCitations: {pages_list}"

            # Save detailed metadata for JavaScript click handler
            nodes_metadata[n["id"]] = {
                "label": n["label"],
                "type": entity_type,
                "color": color,
                "description": desc,
                "docs": docs_list,
                "pages": pages_list
            }

            net.add_node(
                n["id"],
                label=f"<b>{n['label']}</b>",
                title=clean_tooltip,
                color={
                    "background": "#FFFFFF",
                    "border": color,
                    "highlight": {"background": "#F5F3FF", "border": "#7C3AED"},
                    "hover": {"background": "#F4F4F5", "border": color}
                },
                shape="box",
                margin=8,
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

        # Inject interactive click overlay modal inside the network canvas
        metadata_json = json.dumps(nodes_metadata)
        
        custom_script = f"""
        <!-- Interactive Concept Card Overlay on Node Click -->
        <style>
            #concept-card-overlay {{
                position: absolute;
                top: 16px;
                right: 16px;
                width: 320px;
                max-width: 90%;
                max-height: 85%;
                overflow-y: auto;
                background: #FFFFFF;
                border: 1px solid #E4E4E7;
                border-left: 3.5px solid #7C3AED;
                border-radius: 10px;
                padding: 16px 18px;
                box-shadow: 0 10px 25px -5px rgba(24, 24, 27, 0.08), 0 4px 6px -2px rgba(24, 24, 27, 0.03);
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                z-index: 9999;
                display: none;
                transition: opacity 0.15s ease;
            }}
            #concept-card-overlay .card-header {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                margin-bottom: 8px;
            }}
            #concept-card-overlay .card-title {{
                font-size: 15px;
                font-weight: 700;
                color: #18181B;
                line-height: 1.35;
                margin: 0;
            }}
            #concept-card-overlay .card-type {{
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 4px;
                text-transform: uppercase;
                letter-spacing: 0.4px;
                background: #F5F3FF;
                color: #7C3AED;
                margin-left: 6px;
                white-space: nowrap;
            }}
            #concept-card-overlay .card-desc {{
                font-size: 12.5px;
                line-height: 1.55;
                color: #3F3F46;
                background: #FAFAF9;
                border: 1px solid #F4F4F5;
                border-radius: 6px;
                padding: 10px 12px;
                margin: 10px 0;
            }}
            #concept-card-overlay .card-meta {{
                font-size: 11.5px;
                color: #71717A;
                border-top: 1px solid #F4F4F5;
                padding-top: 8px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            #concept-card-overlay .card-meta strong {{
                color: #18181B;
            }}
            #concept-card-overlay .close-btn {{
                background: transparent;
                border: none;
                color: #A1A1AA;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                padding: 0 4px;
                line-height: 1;
            }}
            #concept-card-overlay .close-btn:hover {{
                color: #18181B;
            }}
        </style>

        <div id="concept-card-overlay">
            <div class="card-header">
                <div>
                    <h4 class="card-title" id="card-node-title">Concept Name</h4>
                </div>
                <div style="display: flex; align-items: center;">
                    <span class="card-type" id="card-node-type">CONCEPT</span>
                    <button class="close-btn" onclick="document.getElementById('concept-card-overlay').style.display='none';">&times;</button>
                </div>
            </div>
            <div class="card-desc" id="card-node-desc">
                Definition from document will appear here.
            </div>
            <div class="card-meta">
                <div><strong>Document:</strong> <span id="card-node-doc">-</span></div>
                <div><strong>Citation:</strong> <span id="card-node-cite">-</span></div>
            </div>
        </div>

        <script type="text/javascript">
            const nodeMetaStore = {metadata_json};
            
            if (typeof network !== 'undefined') {{
                network.on("click", function (params) {{
                    const overlay = document.getElementById("concept-card-overlay");
                    if (params.nodes.length > 0) {{
                        const nodeId = params.nodes[0];
                        const meta = nodeMetaStore[nodeId];
                        if (meta) {{
                            document.getElementById("card-node-title").innerText = meta.label;
                            document.getElementById("card-node-type").innerText = meta.type;
                            document.getElementById("card-node-type").style.color = meta.color || '#7C3AED';
                            document.getElementById("card-node-desc").innerText = meta.description || 'No description stored.';
                            document.getElementById("card-node-doc").innerText = meta.docs || 'Unknown';
                            document.getElementById("card-node-cite").innerText = meta.pages || 'N/A';
                            overlay.style.display = "block";
                        }}
                    }}
                }});
            }}
        </script>
        """

        # Append script before closing body
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{custom_script}</body>")
        else:
            html_content += custom_script

        return html_content
