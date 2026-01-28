# Crime Network Editor

This project provides a NiceGUI application for editing and visualizing a crime network graph stored in `data/data.xlsx`. The UI renders an undirected Cytoscape.js graph, offers editable node/edge tables, and exports data to CSV and GEXF.

## Setup

```bash
pip install -r requirements.txt
```

### Windows + Python notes

This project pins `pandas==2.2.2`, which does **not** provide wheels for Python 3.14. If you are on Windows and attempt to install with Python 3.14, `pip` will try to compile pandas from source and fail unless you have the Visual Studio C++ build tools installed. The quickest path is to use Python 3.11 or 3.12 in a virtual environment.

```bat
py install 3.12
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

If you must stay on Python 3.14, install the Visual Studio Build Tools (C++ workload) so pandas can compile from source, but note that 3.14 is pre-release and pandas compatibility may still be incomplete.

## Run

```bash
python app/main.py
```

NiceGUI prints the local URL (default `http://localhost:8080`). Open it in a browser to use the editor.

## Key Features
- Left sidebar filters (node type + relationship), search, and export actions.
- Cytoscape.js force-directed graph with custom icons and tooltips.
- Editable tables for nodes and edges (NiceGUI aggrid) plus inspector edit/delete controls.
- Validation for node IDs and edge references.
- Export to `exports/nodes.csv`, `exports/edges.csv`, and `exports/graph.gexf`.

## Documentation
- `docs/PROJECT_SPEC.md`
- `docs/DATA_SCHEMA.md`
- `docs/WORKFLOW.md`
