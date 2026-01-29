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
            const sources = [
                '/assets/vendor/cytoscape.min.js',
                'https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js',
                'https://cdn.jsdelivr.net/npm/cytoscape@3.26.0/dist/cytoscape.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js',
            ];
            const loadNext = () => {
                if (sources.length === 0) {
                    reject(new Error('Unable to load Cytoscape.js'));
                    return;
                }
                const src = sources.shift();
                const script = document.createElement('script');
                script.src = src;
                script.onload = () => resolve(true);
                script.onerror = () => loadNext();
                document.head.appendChild(script);
            };
            loadNext();
        });
    </script>
    <style>
        :root {
            --surface: #ffffff;
            --surface-muted: #f8fafc;
            --surface-strong: #eef2ff;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-muted: #64748b;
            --accent: #4f46e5;
            --accent-strong: #4338ca;
            --success: #16a34a;
            --danger: #dc2626;
        }
        body {
            background: #1e3a8a;
            color: var(--text-primary);
        }
        .nicegui-content {
            padding: 24px 28px;
        }
        #cy {
            width: 100%;
            height: 640px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: var(--surface-strong);
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
            background: rgba(248, 250, 252, 0.85);
            border-radius: 12px;
            z-index: 5;
        }
        .ag-root-wrapper {
            min-height: 320px;
        }
        .ag-center-cols-viewport {
            min-height: 320px;
        }
        #cy-tooltip {
            position: absolute;
            background: rgba(15, 23, 42, 0.92);
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
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            background: var(--surface);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        }
        .ag-theme-balham,
        .ag-theme-alpine {
            background: var(--surface);
            border-radius: 12px;
        }
        .inspector-card {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            background: var(--surface);
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
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
            background: var(--surface-muted);
            border: 1px solid transparent;
        }
        .q-field--focused .q-field__control {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
        }
        .q-btn {
            border-radius: 12px;
            text-transform: none;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        .q-btn.q-btn--outline {
            color: var(--accent);
            border-color: rgba(79, 70, 229, 0.5);
        }
        .q-btn.q-btn--outline:hover {
            border-color: var(--accent-strong);
        }
        .q-btn:not(.q-btn--outline) {
            background: var(--accent);
            color: white;
        }
        .q-btn:not(.q-btn--outline):hover {
            background: var(--accent-strong);
        }
        .q-btn.bg-negative,
        .q-btn.text-negative {
            background: var(--danger);
            color: white;
        }
        .q-btn.bg-negative:hover,
        .q-btn.text-negative:hover {
            background: #b91c1c;
        }
        .q-separator {
            background: var(--border);
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
        await ui.run_javascript("window.safeResetFilters()", respond=False)

    async def set_grid_rows(grid, rows: list[dict]) -> None:
        await grid.call_api_method("setRowData", rows)

    current_selection: dict[str, dict] = {}

    with ui.row().classes("w-full gap-6"):
        with ui.column().classes("w-1/5 gap-4"):
            ui.label("Filters & Export").classes("text-lg font-semibold panel-title")
            ui.label("Shape what you see and export ready files.").classes(
                "text-sm panel-subtitle"
            )
            with ui.column().classes("sidebar-section gap-4"):
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

        with ui.column().classes("w-3/5 gap-4"):
            ui.label("Crime Network Graph").classes("text-lg font-semibold panel-title")
            ui.label("Explore relationships in a cleaner, calmer layout.").classes(
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

                    const runLayout = () => {{
                        if (!window.cy) return;
                        const layout = window.cy.layout(buildLayout());
                        layout.run();
                        layout.on('layoutstop', () => {{
                            window.cy.fit(undefined, 40);
                        }});
                    }};

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
                        const statusEl = document.getElementById('cy-status');
                        if (window.cytoscapeLoad && !window.cytoscapeLoadHandled) {{
                            window.cytoscapeLoadHandled = true;
                            window.cytoscapeLoad.catch(() => {{
                                const fallbackContainer = document.getElementById('cy');
                                if (fallbackContainer) {{
                                    fallbackContainer.innerHTML = `
                                        <div style="padding: 16px; text-align: center; color: #b91c1c;">
                                            Unable to load Cytoscape.js. Check network access or allow the CDN.
                                        </div>
                                    `;
                                }}
                                if (statusEl) {{
                                    statusEl.textContent =
                                        'Graph library failed to load. Ensure Cytoscape.js is reachable or add assets/vendor/cytoscape.min.js.';
                                }}
                            }});
                        }}
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
                                        'background-color': '#ffffff',
                                        'border-width': 1,
                                        'border-color': '#a5b4fc',
                                        'width': 56,
                                        'height': 56,
                                        'label': 'data(label)',
                                        'text-valign': 'bottom',
                                        'text-margin-y': 8,
                                        'font-size': 11,
                                        'color': '#0f172a',
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
                                        'line-color': '#c7d2fe',
                                        'curve-style': 'straight',
                                    }}
                                }}
                            ],
                            layout: buildLayout(),
                        }});
                        cy.ready(() => {{
                            cy.resize();
                            cy.fit(undefined, 40);
                            if (statusEl) {{
                                statusEl.style.display = 'none';
                            }}
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
                        runLayout();
                    }};

                    window.applyFilters = (query, types, relationships) => {{
                        if (!window.cy) {{
                            window.pendingFilters = {{ query, types, relationships }};
                            initCytoscape();
                            return;
                        }}
                        applyFiltersToGraph(query, types, relationships);
                        runLayout();
                    }};

                    window.resetFilters = () => {{
                        if (!window.cy) {{
                            window.pendingFilters = {{ query: '', types: [], relationships: [] }};
                            initCytoscape();
                            return;
                        }}
                        window.cy.nodes().style('display', 'element');
                        window.cy.edges().style('display', 'element');
                        runLayout();
                    }};

                    window.safeApplyFilters = (query, types, relationships) => {{
                        if (typeof window.applyFilters !== 'function') {{
                            console.error('applyFilters is not ready yet.');
                            return;
                        }}
                        window.applyFilters(query, types, relationships);
                    }};

                    window.safeResetFilters = () => {{
                        if (typeof window.resetFilters !== 'function') {{
                            console.error('resetFilters is not ready yet.');
                            return;
                        }}
                        window.resetFilters();
                    }};

                    initCytoscape();
                    setTimeout(() => {{
                        if (!window.cy) {{
                            const statusEl = document.getElementById('cy-status');
                            if (statusEl) {{
                                statusEl.textContent =
                                    'Graph is still loading. If it stays blank, allow a Cytoscape CDN or add assets/vendor/cytoscape.min.js.';
                            }}
                        }}
                    }}, 3000);
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

        with ui.column().classes("w-1/5 gap-4"):
            ui.label("Inspector").classes("text-lg font-semibold panel-title")
            ui.label("Quickly review or edit selections.").classes("text-sm panel-subtitle")
            with ui.column().classes("inspector-card gap-2"):
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
