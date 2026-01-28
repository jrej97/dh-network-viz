# Crime Network Editor

This project provides a NiceGUI application for editing and visualizing a crime network graph stored in `data/data.xlsx`. The UI renders an undirected Cytoscape.js graph, offers editable node/edge tables, and exports data to CSV and GEXF.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app/main.py
```

NiceGUI prints the local URL (default `http://localhost:8080`). Open it in a browser to use the editor.

## Key Features
- Left sidebar filters, search, and export actions.
- Cytoscape.js force-directed graph with custom icons and tooltips.
- Editable tables for nodes and edges (NiceGUI aggrid).
- Validation for node IDs and edge references.
- Export to `exports/nodes.csv`, `exports/edges.csv`, and `exports/graph.gexf`.

## Documentation
- `docs/PROJECT_SPEC.md`
- `docs/DATA_SCHEMA.md`
- `docs/WORKFLOW.md`
