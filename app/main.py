from __future__ import annotations

import json
from pathlib import Path

from nicegui import app, ui

from data_io import export_data, load_data, rows_to_dataframes, save_data, validate_data
from graph_utils import build_elements

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "data.xlsx"
EXPORTS_DIR = BASE_DIR / "exports"

app.add_static_files("/assets", BASE_DIR / "assets")

ui.add_head_html(
    """
    <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
    <style>
        #cy {
            width: 100%;
            height: 640px;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            background: #f9fafb;
        }
        #cy-tooltip {
            position: absolute;
            background: rgba(17, 24, 39, 0.9);
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            max-width: 240px;
            z-index: 10;
        }
        .sidebar-section {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            background: white;
        }
        .inspector-card {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            background: white;
        }
    </style>
    """
)


@ui.page("/")
async def main() -> None:
    nodes_df, edges_df = load_data(DATA_PATH)

    state = {
        "nodes": nodes_df,
        "edges": edges_df,
    }

    async def refresh_graph() -> None:
        elements = build_elements(state["nodes"], state["edges"])
        await ui.run_javascript(
            "updateGraph(%s)" % json.dumps(elements)
        )

    async def collect_grid_data() -> tuple[list[dict], list[dict]]:
        nodes_rows = await nodes_grid.get_row_data()
        edges_rows = await edges_grid.get_row_data()
        return nodes_rows or [], edges_rows or []

    async def on_save() -> None:
        nodes_rows, edges_rows = await collect_grid_data()
        nodes_df_new, edges_df_new = rows_to_dataframes(nodes_rows, edges_rows)
        errors = validate_data(nodes_df_new, edges_df_new)
        if errors:
            ui.notify("Validation failed: " + " ".join(errors), color="negative")
            return
        save_data(DATA_PATH, nodes_df_new, edges_df_new)
        state["nodes"] = nodes_df_new
        state["edges"] = edges_df_new
        await refresh_graph()
        ui.notify("Excel saved and graph updated.", color="positive")

    async def on_export() -> None:
        nodes_rows, edges_rows = await collect_grid_data()
        nodes_df_new, edges_df_new = rows_to_dataframes(nodes_rows, edges_rows)
        errors = validate_data(nodes_df_new, edges_df_new)
        if errors:
            ui.notify("Validation failed: " + " ".join(errors), color="negative")
            return
        save_data(DATA_PATH, nodes_df_new, edges_df_new)
        export_paths = export_data(EXPORTS_DIR, nodes_df_new, edges_df_new)
        ui.notify(
            "Exports created: "
            f"{export_paths['nodes'].name}, {export_paths['edges'].name}, {export_paths['gexf'].name}.",
            color="positive",
        )

    async def apply_filters() -> None:
        await ui.run_javascript(
            "applyFilters(%s, %s)" % (json.dumps(search_input.value), json.dumps(type_filter.value))
        )

    async def reset_filters() -> None:
        search_input.value = ""
        type_filter.value = []
        await ui.run_javascript("resetFilters()")

    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/5 gap-4"):
            ui.label("Filters & Export").classes("text-lg font-semibold")
            with ui.column().classes("sidebar-section gap-4"):
                search_input = ui.input("Search nodes")
                type_filter = ui.select(
                    ["Person", "Place", "Institution", "Group"],
                    label="Filter by type",
                    multiple=True,
                )
                ui.button("Apply Filters", on_click=apply_filters)
                ui.button("Reset Filters", on_click=reset_filters).props("outline")
                ui.separator()
                ui.button("Save to Excel", on_click=on_save)
                ui.button("Export CSV + GEXF", on_click=on_export).props("outline")

        with ui.column().classes("w-3/5 gap-4"):
            ui.label("Crime Network Graph").classes("text-lg font-semibold")
            elements = build_elements(state["nodes"], state["edges"])
            ui.html(
                f"""
                <div style="position: relative;">
                    <div id="cy"></div>
                    <div id="cy-tooltip"></div>
                </div>
                <script>
                    const cy = window.cy = cytoscape({{
                        container: document.getElementById('cy'),
                        elements: {json.dumps(elements)},
                        style: [
                            {{
                                selector: 'node',
                                style: {{
                                    'shape': 'ellipse',
                                    'background-color': '#ffffff',
                                    'border-width': 1,
                                    'border-color': '#d1d5db',
                                    'width': 56,
                                    'height': 56,
                                    'label': 'data(label)',
                                    'text-valign': 'bottom',
                                    'text-margin-y': 8,
                                    'font-size': 11,
                                    'color': '#374151',
                                    'background-image': 'data(icon)',
                                    'background-fit': 'contain',
                                    'background-clip': 'none',
                                    'background-opacity': 0,
                                }}
                            }},
                            {{
                                selector: 'edge',
                                style: {{
                                    'width': 1,
                                    'line-color': '#d1d5db',
                                    'curve-style': 'straight',
                                }}
                            }}
                        ],
                        layout: {{
                            name: 'cose',
                            animate: false,
                            nodeRepulsion: 6000,
                            idealEdgeLength: 140,
                            componentSpacing: 160,
                        }},
                    }});

                    const tooltip = document.getElementById('cy-tooltip');
                    cy.on('mouseover', 'node', (event) => {{
                        const node = event.target;
                        const description = node.data('description');
                        if (!description) return;
                        tooltip.textContent = description;
                        tooltip.style.display = 'block';
                        tooltip.style.left = `${{event.renderedPosition.x + 12}}px`;
                        tooltip.style.top = `${{event.renderedPosition.y + 12}}px`;
                    }});
                    cy.on('mouseout', 'node', () => {{
                        tooltip.style.display = 'none';
                    }});
                    cy.on('tap', 'node', (event) => {{
                        const node = event.target;
                        window.dispatchEvent(new CustomEvent('cy_selected', {{
                            detail: {{ kind: 'node', data: node.data() }}
                        }}));
                    }});
                    cy.on('tap', 'edge', (event) => {{
                        const edge = event.target;
                        window.dispatchEvent(new CustomEvent('cy_selected', {{
                            detail: {{ kind: 'edge', data: edge.data() }}
                        }}));
                    }});

                    window.updateGraph = (elements) => {{
                        cy.elements().remove();
                        cy.add(elements);
                        cy.layout({{
                            name: 'cose',
                            animate: false,
                            nodeRepulsion: 6000,
                            idealEdgeLength: 140,
                            componentSpacing: 160,
                        }}).run();
                    }};

                    window.applyFilters = (query, types) => {{
                        const normalizedQuery = (query || '').toLowerCase();
                        const typeSet = new Set((types || []).map((value) => value.toLowerCase()));
                        cy.nodes().forEach((node) => {{
                            const matchesQuery = node.data('label').toLowerCase().includes(normalizedQuery);
                            const matchesType = typeSet.size === 0 || typeSet.has(node.data('type').toLowerCase());
                            node.style('display', matchesQuery && matchesType ? 'element' : 'none');
                        }});
                        cy.edges().forEach((edge) => {{
                            const sourceVisible = edge.source().style('display') !== 'none';
                            const targetVisible = edge.target().style('display') !== 'none';
                            edge.style('display', sourceVisible && targetVisible ? 'element' : 'none');
                        }});
                    }};

                    window.resetFilters = () => {{
                        cy.nodes().style('display', 'element');
                        cy.edges().style('display', 'element');
                    }};
                </script>
                """
            )

            with ui.expansion("Edit Nodes", icon="edit"):
                nodes_grid = ui.aggrid(
                    {
                        "columnDefs": [
                            {"headerName": "ID", "field": "id", "editable": True},
                            {"headerName": "Label", "field": "label", "editable": True},
                            {
                                "headerName": "Type",
                                "field": "type",
                                "editable": True,
                                "cellEditor": "agSelectCellEditor",
                                "cellEditorParams": {
                                    "values": ["Person", "Place", "Institution", "Group"]
                                },
                            },
                            {"headerName": "Description", "field": "description", "editable": True},
                        ],
                        "rowData": state["nodes"].to_dict(orient="records"),
                        "defaultColDef": {"flex": 1, "resizable": True},
                        "stopEditingWhenCellsLoseFocus": True,
                    }
                ).classes("w-full h-64")

            with ui.expansion("Edit Edges", icon="edit"):
                edges_grid = ui.aggrid(
                    {
                        "columnDefs": [
                            {"headerName": "Source", "field": "source", "editable": True},
                            {"headerName": "Target", "field": "target", "editable": True},
                            {
                                "headerName": "Relationship",
                                "field": "relationship_type",
                                "editable": True,
                            },
                            {"headerName": "Description", "field": "description", "editable": True},
                        ],
                        "rowData": state["edges"].to_dict(orient="records"),
                        "defaultColDef": {"flex": 1, "resizable": True},
                        "stopEditingWhenCellsLoseFocus": True,
                    }
                ).classes("w-full h-64")

        with ui.column().classes("w-1/5 gap-4"):
            ui.label("Inspector").classes("text-lg font-semibold")
            with ui.column().classes("inspector-card gap-2"):
                inspector_title = ui.label("Select a node or edge")
                inspector_type = ui.label("Type: -")
                inspector_meta = ui.label("Details: -")

    def handle_selection(event) -> None:
        detail = event.args
        if not detail:
            return
        kind = detail.get("kind")
        data = detail.get("data", {})
        if kind == "node":
            inspector_title.text = data.get("label", "Node")
            inspector_type.text = f"Type: {data.get('type', '-') }"
            inspector_meta.text = data.get("description") or "No description"
        elif kind == "edge":
            inspector_title.text = f"{data.get('source')} ↔ {data.get('target')}"
            inspector_type.text = f"Relationship: {data.get('relationship_type', '-') }"
            inspector_meta.text = data.get("description") or "No description"

    ui.on("cy_selected", handle_selection)


ui.run(title="Crime Network Editor", port=8080, reload=False)
