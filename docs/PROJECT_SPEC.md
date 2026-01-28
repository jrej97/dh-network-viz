# Crime Network Visualization Project Specification

## Goal
Provide a NiceGUI application that lets analysts edit a network graph stored in `data/data.xlsx`, visualize it as an undirected Cytoscape.js diagram, and export the data to CSV and GEXF for downstream tooling.

## Functional Requirements
- Load nodes/edges from the Excel workbook.
- Render an undirected, force-directed graph with a clean crime-network aesthetic.
- Provide editable tables for nodes and edges.
- Validate node IDs and edge references before saving.
- Persist edits back to the Excel source of truth.
- Export nodes/edges to CSV and the graph to GEXF.

## UX Layout
- **Left sidebar:** filters/search and export/save actions.
- **Center:** Cytoscape.js visualization and editable data tables.
- **Right sidebar:** inspector for selected nodes/edges.

## Key Libraries
- NiceGUI for UI and routing.
- Cytoscape.js for graph rendering.
- pandas + openpyxl for Excel IO.
- networkx for GEXF export.
