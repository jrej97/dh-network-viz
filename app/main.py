from __future__ import annotations

import json
from pathlib import Path

from nicegui import app, ui

from data_io import (
    EDGE_COLUMNS,
    NODE_COLUMNS,
    export_data,
    load_data,
    rows_to_dataframes,
    save_data,
    validate_data,
)
from graph_utils import build_elements

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "data.xlsx"
EXPORTS_DIR = BASE_DIR / "exports"

app.add_static_files("/assets", BASE_DIR / "assets")

ui.add_head_html(
    """
    <script>
        window.cytoscapeLoad = new Promise((resolve, reject) => {
            const primary = document.createElement('script');
            primary.src = 'https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js';
            primary.onload = () => resolve(true);
            primary.onerror = () => {
                const fallback = document.createElement('script');
                fallback.src = 'https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js';
                fallback.onload = () => resolve(true);
                fallback.onerror = () => reject(new Error('Unable to load Cytoscape.js'));
                document.head.appendChild(fallback);
            };
            document.head.appendChild(primary);
        });
    </script>
    <style>
        :root {
            --surface: #0f172a;
            --surface-muted: #111827;
            --surface-strong: #0b1220;
            --border: #1f2937;
            --text-primary: #e5e7eb;
            --text-muted: #9ca3af;
            --accent: #38bdf8;
            --accent-strong: #0284c7;
            --success: #22c55e;
            --danger: #f97316;
        }
        body {
            background: #0b111b;
            color: var(--text-primary);
        }
        .nicegui-content {
            padding: 20px 24px 32px;
        }
        .app-shell {
            max-width: 1400px;
            margin: 0 auto;
        }
        .top-bar {
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 18px;
            box-shadow: 0 16px 32px rgba(2, 6, 23, 0.5);
        }
        .top-pill {
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            letter-spacing: 0.02em;
        }
        #cy {
            width: 100%;
            height: 640px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 18px;
            background: radial-gradient(circle at 20% 20%, #0f172a 0%, #0b1220 45%, #060b15 100%);
            position: relative;
        }
        #cy-status {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            color: var(--text-muted);
            background: rgba(5, 8, 16, 0.7);
            border-radius: 18px;
            z-index: 5;
        }
        #cy-tooltip {
            position: absolute;
            background: rgba(2, 6, 23, 0.92);
            color: #e2e8f0;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            max-width: 240px;
            z-index: 10;
        }
        .panel-card {
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            background: rgba(15, 23, 42, 0.92);
            box-shadow: 0 14px 32px rgba(2, 6, 23, 0.6);
        }
        .ag-theme-balham,
        .ag-theme-alpine {
            background: rgba(15, 23, 42, 0.92);
            border-radius: 12px;
            color: var(--text-primary);
        }
        .panel-title {
            color: var(--text-primary);
            letter-spacing: -0.01em;
        }
        .panel-subtitle {
            color: var(--text-muted);
        }
        .q-field__control {
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: var(--text-primary);
        }
        .q-field--focused .q-field__control {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
        }
        .q-field__native,
        .q-field__input,
        .q-field__label {
            color: var(--text-primary);
        }
        .q-btn {
            border-radius: 12px;
            text-transform: none;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .q-btn.q-btn--outline {
            color: var(--accent);
            border-color: rgba(56, 189, 248, 0.6);
        }
        .q-btn.q-btn--outline:hover {
            border-color: var(--accent-strong);
        }
        .q-btn:not(.q-btn--outline) {
            background: var(--accent);
            color: #0b111b;
        }
        .q-btn:not(.q-btn--outline):hover {
            background: var(--accent-strong);
        }
        .q-btn.bg-negative,
        .q-btn.text-negative {
            background: var(--danger);
            color: #0b111b;
        }
        .q-btn.bg-negative:hover,
        .q-btn.text-negative:hover {
            background: #ea580c;
        }
        .q-separator {
            background: var(--border);
        }
        .ag-root-wrapper,
        .ag-center-cols-viewport {
            min-height: 320px;
        }
    </style>
    """
)


@ui.page("/")
async def main() -> None:
    try:
        nodes_df, edges_df = load_data(DATA_PATH)
    except Exception as exc:
        ui.label("Unable to load the Excel workbook.").classes("text-lg font-semibold")
        ui.label(str(exc)).classes("text-red-600")
        ui.label(
            "Check that data/data.xlsx exists and contains 'nodes' and 'edges' sheets with required columns."
        )
        return

    state = {
        "nodes": nodes_df,
        "edges": edges_df,
    }

    node_columns = state["nodes"].columns.tolist()
    edge_columns = state["edges"].columns.tolist()

    async def refresh_graph() -> None:
        elements = build_elements(state["nodes"], state["edges"])
        await ui.run_javascript(
            "updateGraph(%s)" % json.dumps(elements),
            respond=False,
        )

    async def collect_grid_data() -> tuple[list[dict], list[dict]]:
        nodes_rows = await nodes_grid.get_row_data()
        edges_rows = await edges_grid.get_row_data()
        return nodes_rows or [], edges_rows or []

    async def sync_state_from_grids() -> None:
        nodes_rows, edges_rows = await collect_grid_data()
        nodes_df_new, edges_df_new = rows_to_dataframes(
            nodes_rows, edges_rows, node_columns, edge_columns
        )
        state["nodes"] = nodes_df_new
        state["edges"] = edges_df_new

    async def on_save() -> None:
        nodes_rows, edges_rows = await collect_grid_data()
        nodes_df_new, edges_df_new = rows_to_dataframes(
            nodes_rows, edges_rows, node_columns, edge_columns
        )
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
        nodes_df_new, edges_df_new = rows_to_dataframes(
            nodes_rows, edges_rows, node_columns, edge_columns
        )
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
            "window.safeApplyFilters(%s, %s, %s)"
            % (
                json.dumps(search_input.value),
                json.dumps(type_filter.value),
                json.dumps(relationship_filter.value),
            ),
            respond=False,
        )

    async def reset_filters() -> None:
        search_input.value = ""
        type_filter.value = []
        relationship_filter.value = []
        await ui.run_javascript("resetFilters()", respond=False)

    async def set_grid_rows(grid, rows: list[dict]) -> None:
        await grid.call_api_method("setRowData", rows)

    current_selection: dict[str, dict] = {}

    with ui.column().classes("w-full gap-6 app-shell"):
        with ui.row().classes("w-full items-center justify-between top-bar"):
            with ui.column().classes("gap-1"):
                ui.label("Gephi Lite — Network Studio").classes("text-lg font-semibold")
                ui.label("Interactive graph editing inspired by lite.gephi.org").classes(
                    "text-xs panel-subtitle"
                )
            with ui.row().classes("items-center gap-2"):
                ui.label("Live").classes("top-pill")
                ui.label("Cytoscape.js").classes("top-pill")
                ui.label("NiceGUI").classes("top-pill")

        with ui.row().classes("w-full gap-6"):
            with ui.column().classes("w-1/4 gap-4"):
                ui.label("Filters & Export").classes("text-lg font-semibold panel-title")
                ui.label("Curate the graph view and output files.").classes(
                    "text-sm panel-subtitle"
                )
                with ui.column().classes("panel-card gap-4"):
                    search_input = ui.input("Search nodes")
                    type_filter = ui.select(
                        ["Person", "Place", "Institution", "Group"],
                        label="Filter by type",
                        multiple=True,
                    )
                    relationship_filter = ui.select(
                        sorted(
                            {
                                value
                                for value in state["edges"]["relationship_type"].astype(str).tolist()
                                if value
                            }
                        ),
                        label="Filter by relationship",
                        multiple=True,
                    )
                    ui.button("Apply Filters", on_click=apply_filters)
                    ui.button("Reset Filters", on_click=reset_filters).props("outline")
                    ui.separator()
                    ui.button("Save to Excel", on_click=on_save)
                    ui.button("Export CSV + GEXF", on_click=on_export).props("outline")

            with ui.column().classes("w-1/2 gap-4"):
                ui.label("Graph View").classes("text-lg font-semibold panel-title")
                ui.label("Zoom, pan, and select nodes to inspect metadata.").classes(
                    "text-sm panel-subtitle"
                )
                elements = build_elements(state["nodes"], state["edges"])
                ui.html(
                    """
                    <div style="position: relative;">
                        <div id="cy"></div>
                        <div id="cy-status">Loading graph…</div>
                        <div id="cy-tooltip"></div>
                    </div>
                    """
                )
            elements_json = json.dumps(elements)
            ui.add_body_html(
                f"""
                <script>
                    window.pendingElements = {elements_json};
                    window.pendingFilters = null;

                    const buildLayout = () => ({{
                        name: 'cose',
                        animate: false,
                        nodeRepulsion: 6000,
                        idealEdgeLength: 140,
                        componentSpacing: 160,
                    }});

                    const applyFiltersToGraph = (query, types, relationships) => {{
                        if (!window.cy) return;
                        const normalizedQuery = (query || '').toLowerCase();
                        const typeSet = new Set((types || []).map((value) => value.toLowerCase()));
                        const relationSet = new Set((relationships || []).map((value) => value.toLowerCase()));
                        window.cy.nodes().forEach((node) => {{
                            const label = (node.data('label') || '').toLowerCase();
                            const nodeType = (node.data('type') || '').toLowerCase();
                            const matchesQuery = label.includes(normalizedQuery);
                            const matchesType = typeSet.size === 0 || typeSet.has(nodeType);
                            node.style('display', matchesQuery && matchesType ? 'element' : 'none');
                        }});
                        window.cy.edges().forEach((edge) => {{
                            const sourceVisible = edge.source().style('display') !== 'none';
                            const targetVisible = edge.target().style('display') !== 'none';
                            const relationship = (edge.data('relationship_type') || '').toLowerCase();
                            const matchesRelation =
                                relationSet.size === 0 || relationSet.has(relationship);
                            edge.style(
                                'display',
                                sourceVisible && targetVisible && matchesRelation ? 'element' : 'none'
                            );
                        }});
                        if (relationSet.size > 0) {{
                            window.cy.nodes().forEach((node) => {{
                                const connectedVisible =
                                    node.connectedEdges().filter(
                                        (edge) => edge.style('display') !== 'none'
                                    ).length > 0;
                                if (!connectedVisible) {{
                                    node.style('display', 'none');
                                }}
                            }});
                        }}
                    }};

                    const initCytoscape = () => {{
                        if (window.cy) return;
                        if (typeof cytoscape === 'undefined') {{
                            setTimeout(initCytoscape, 50);
                            return;
                        }}
                        const container = document.getElementById('cy');
                        if (!container) {{
                            setTimeout(initCytoscape, 50);
                            return;
                        }}

                        const cy = window.cy = cytoscape({{
                            container,
                            elements: window.pendingElements || [],
                            style: [
                                {{
                                    selector: 'node',
                                    style: {{
                                        'shape': 'ellipse',
                                        'background-color': '#0f172a',
                                        'border-width': 1.5,
                                        'border-color': '#38bdf8',
                                        'width': 52,
                                        'height': 52,
                                        'label': 'data(label)',
                                        'text-valign': 'bottom',
                                        'text-margin-y': 8,
                                        'font-size': 11,
                                        'color': '#e2e8f0',
                                        'background-image': 'data(icon)',
                                        'background-fit': 'contain',
                                        'background-clip': 'none',
                                        'background-opacity': 0,
                                    }}
                                }},
                                {{
                                    selector: 'edge',
                                    style: {{
                                        'width': 1.2,
                                        'line-color': '#334155',
                                        'curve-style': 'straight',
                                    }}
                                }}
                            ],
                            layout: buildLayout(),
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
                        cy.on('mouseover', 'edge', (event) => {{
                            const edge = event.target;
                            const relationship = edge.data('relationship_type');
                            const description = edge.data('description');
                            if (!relationship && !description) return;
                            tooltip.textContent = [relationship, description].filter(Boolean).join(': ');
                            tooltip.style.display = 'block';
                            tooltip.style.left = `${{event.renderedPosition.x + 12}}px`;
                            tooltip.style.top = `${{event.renderedPosition.y + 12}}px`;
                        }});
                        cy.on('mouseout', 'edge', () => {{
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

                        if (window.pendingFilters) {{
                            applyFiltersToGraph(
                                window.pendingFilters.query,
                                window.pendingFilters.types,
                                window.pendingFilters.relationships
                            );
                            window.pendingFilters = null;
                        }}
                    }};

                    window.updateGraph = (elements) => {{
                        window.pendingElements = elements;
                        if (!window.cy) {{
                            initCytoscape();
                            return;
                        }}
                        window.cy.elements().remove();
                        window.cy.add(elements);
                        window.cy.layout(buildLayout()).run();
                    }};

                    window.applyFilters = (query, types, relationships) => {{
                        if (!window.cy) {{
                            window.pendingFilters = {{ query, types, relationships }};
                            initCytoscape();
                            return;
                        }}
                        applyFiltersToGraph(query, types, relationships);
                    }};

                    window.resetFilters = () => {{
                        if (!window.cy) {{
                            window.pendingFilters = {{ query: '', types: [], relationships: [] }};
                            initCytoscape();
                            return;
                        }}
                        window.cy.nodes().style('display', 'element');
                        window.cy.edges().style('display', 'element');
                    }};

                    initCytoscape();
                </script>
                """
            )

            def build_column_defs(columns: list[str], core_columns: list[str]) -> list[dict]:
                defs: list[dict] = []
                for column in columns:
                    header_name = column.replace("_", " ").title()
                    column_def: dict = {"headerName": header_name, "field": column, "editable": True}
                    if column == "type":
                        column_def["cellEditor"] = "agSelectCellEditor"
                        column_def["cellEditorParams"] = {
                            "values": ["Person", "Place", "Institution", "Group"]
                        }
                    if column not in core_columns:
                        column_def["hide"] = True
                    defs.append(column_def)
                return defs

            with ui.expansion("Edit Nodes", icon="edit"):
                nodes_grid = ui.aggrid(
                    {
                        "columnDefs": build_column_defs(node_columns, NODE_COLUMNS),
                        "rowData": state["nodes"].to_dict(orient="records"),
                        "defaultColDef": {"flex": 1, "resizable": True},
                        "stopEditingWhenCellsLoseFocus": True,
                    }
                ).classes("w-full h-96")

            with ui.expansion("Edit Edges", icon="edit"):
                edges_grid = ui.aggrid(
                    {
                        "columnDefs": build_column_defs(edge_columns, EDGE_COLUMNS),
                        "rowData": state["edges"].to_dict(orient="records"),
                        "defaultColDef": {"flex": 1, "resizable": True},
                        "stopEditingWhenCellsLoseFocus": True,
                    }
                ).classes("w-full h-96")

            with ui.column().classes("w-1/4 gap-4"):
                ui.label("Inspector").classes("text-lg font-semibold panel-title")
                ui.label("Select nodes or edges to inspect and edit.").classes(
                    "text-sm panel-subtitle"
                )
                with ui.column().classes("panel-card gap-2"):
                    inspector_title = ui.label("Select a node or edge")
                    inspector_type = ui.label("Type: -")
                    inspector_meta = ui.label("Details: -")
                    with ui.row().classes("gap-2"):
                        edit_button = ui.button("Edit").props("outline")
                        delete_button = ui.button("Delete").props("outline color=negative")

    def handle_selection(event) -> None:
        detail = event.args
        if not detail:
            return
        kind = detail.get("kind")
        data = detail.get("data", {})
        current_selection.clear()
        current_selection.update({"kind": kind, "data": data})
        if kind == "node":
            inspector_title.text = data.get("label", "Node")
            inspector_type.text = f"Type: {data.get('type', '-') }"
            inspector_meta.text = data.get("description") or "No description"
        elif kind == "edge":
            inspector_title.text = f"{data.get('source')} ↔ {data.get('target')}"
            inspector_type.text = f"Relationship: {data.get('relationship_type', '-') }"
            inspector_meta.text = data.get("description") or "No description"

    ui.on("cy_selected", handle_selection)

    async def on_edit() -> None:
        if not current_selection:
            ui.notify("Select a node or edge first.", color="warning")
            return
        kind = current_selection.get("kind")
        data = current_selection.get("data", {})
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Edit {kind}")
            if kind == "node":
                id_input = ui.input("ID", value=data.get("id", ""))
                label_input = ui.input("Label", value=data.get("label", ""))
                type_input = ui.select(
                    ["Person", "Place", "Institution", "Group"],
                    value=data.get("type", ""),
                    label="Type",
                )
                desc_input = ui.input("Description", value=data.get("description", ""))

                async def save_node() -> None:
                    nodes_rows = await nodes_grid.get_row_data()
                    edges_rows = await edges_grid.get_row_data()
                    for row in nodes_rows:
                        if str(row.get("id")) == str(data.get("id")):
                            old_id = str(row.get("id"))
                            new_id = id_input.value
                            row["id"] = new_id
                            row["label"] = label_input.value
                            row["type"] = type_input.value
                            row["description"] = desc_input.value
                            if old_id != new_id:
                                for edge_row in edges_rows:
                                    if str(edge_row.get("source")) == old_id:
                                        edge_row["source"] = new_id
                                    if str(edge_row.get("target")) == old_id:
                                        edge_row["target"] = new_id
                            break
                    await set_grid_rows(nodes_grid, nodes_rows)
                    await set_grid_rows(edges_grid, edges_rows)
                    await sync_state_from_grids()
                    await refresh_graph()
                    dialog.close()

                ui.button("Save", on_click=save_node)
            elif kind == "edge":
                source_input = ui.input("Source", value=data.get("source", ""))
                target_input = ui.input("Target", value=data.get("target", ""))
                relation_input = ui.input(
                    "Relationship", value=data.get("relationship_type", "")
                )
                desc_input = ui.input("Description", value=data.get("description", ""))

                async def save_edge() -> None:
                    edges_rows = await edges_grid.get_row_data()
                    updated = False
                    for row in edges_rows:
                        if (
                            str(row.get("source")) == str(data.get("source"))
                            and str(row.get("target")) == str(data.get("target"))
                            and str(row.get("relationship_type"))
                            == str(data.get("relationship_type"))
                            and str(row.get("description")) == str(data.get("description"))
                        ):
                            row["source"] = source_input.value
                            row["target"] = target_input.value
                            row["relationship_type"] = relation_input.value
                            row["description"] = desc_input.value
                            updated = True
                            break
                    if not updated and "row_index" in data:
                        index = int(data["row_index"])
                        if 0 <= index < len(edges_rows):
                            edges_rows[index]["source"] = source_input.value
                            edges_rows[index]["target"] = target_input.value
                            edges_rows[index]["relationship_type"] = relation_input.value
                            edges_rows[index]["description"] = desc_input.value
                    await set_grid_rows(edges_grid, edges_rows)
                    await sync_state_from_grids()
                    await refresh_graph()
                    dialog.close()

                ui.button("Save", on_click=save_edge)
            ui.button("Cancel", on_click=dialog.close).props("outline")

        dialog.open()

    async def on_delete() -> None:
        if not current_selection:
            ui.notify("Select a node or edge first.", color="warning")
            return
        kind = current_selection.get("kind")
        data = current_selection.get("data", {})
        if kind == "node":
            nodes_rows = await nodes_grid.get_row_data()
            node_id = str(data.get("id"))
            nodes_rows = [row for row in nodes_rows if str(row.get("id")) != node_id]
            edges_rows = await edges_grid.get_row_data()
            edges_rows = [
                row
                for row in edges_rows
                if str(row.get("source")) != node_id and str(row.get("target")) != node_id
            ]
            await set_grid_rows(nodes_grid, nodes_rows)
            await set_grid_rows(edges_grid, edges_rows)
        elif kind == "edge":
            edges_rows = await edges_grid.get_row_data()
            filtered_rows = [
                row
                for row in edges_rows
                if not (
                    str(row.get("source")) == str(data.get("source"))
                    and str(row.get("target")) == str(data.get("target"))
                    and str(row.get("relationship_type"))
                    == str(data.get("relationship_type"))
                    and str(row.get("description")) == str(data.get("description"))
                )
            ]
            if len(filtered_rows) == len(edges_rows) and "row_index" in data:
                index = int(data["row_index"])
                if 0 <= index < len(edges_rows):
                    filtered_rows = [
                        row for idx, row in enumerate(edges_rows) if idx != index
                    ]
            await set_grid_rows(edges_grid, filtered_rows)
        await sync_state_from_grids()
        await refresh_graph()

    edit_button.on("click", on_edit)
    delete_button.on("click", on_delete)


ui.run(title="Crime Network Editor", port=8080, reload=False)
