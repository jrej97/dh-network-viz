# Workflow

## Run the App
1. Install dependencies: `pip install -r requirements.txt`.
2. Start the NiceGUI server: `python app/main.py`.
3. Open the URL printed in the console (default: http://localhost:8080).

## Edit Data
1. Use the **Edit Nodes** and **Edit Edges** tables to modify the graph.
2. Click **Save to Excel** to validate and persist changes back to `data/data.xlsx`.
3. The Cytoscape graph refreshes after a successful save.

## Filter and Inspect
- Use the search field or type filter to highlight subsets of the graph.
- Click a node or edge to view details in the inspector.
- Hover nodes to see tooltip descriptions.

## Export
- Click **Export CSV + GEXF** to write:
  - `exports/nodes.csv`
  - `exports/edges.csv`
  - `exports/graph.gexf`
