from __future__ import annotations

from pathlib import Path
from typing import Iterable

import networkx as nx
import pandas as pd

NODE_COLUMNS = ["id", "label", "type", "description"]
EDGE_COLUMNS = ["source", "target", "relationship_type", "description"]


def load_data(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes_df = pd.read_excel(path, sheet_name="nodes")[NODE_COLUMNS]
    edges_df = pd.read_excel(path, sheet_name="edges")[EDGE_COLUMNS]
    nodes_df = nodes_df.fillna("")
    edges_df = edges_df.fillna("")
    return nodes_df, edges_df


def _normalize_df(rows: Iterable[dict], columns: list[str]) -> pd.DataFrame:
    normalized: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        cleaned = {column: str(row.get(column, "")).strip() for column in columns}
        if all(value == "" for value in cleaned.values()):
            continue
        normalized.append(cleaned)
    return pd.DataFrame(normalized, columns=columns)


def validate_data(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    node_ids = nodes_df["id"].astype(str).str.strip()
    if node_ids.eq("").any():
        errors.append("Every node must have a non-empty id.")
    duplicates = node_ids[node_ids.duplicated()].unique().tolist()
    if duplicates:
        errors.append(f"Duplicate node ids found: {', '.join(duplicates)}.")
    node_id_set = set(node_ids)
    missing_sources = edges_df[~edges_df["source"].isin(node_id_set)]["source"].unique()
    missing_targets = edges_df[~edges_df["target"].isin(node_id_set)]["target"].unique()
    if len(missing_sources) > 0:
        errors.append(
            "Edges have missing source ids: " + ", ".join(sorted(map(str, missing_sources)))
        )
    if len(missing_targets) > 0:
        errors.append(
            "Edges have missing target ids: " + ", ".join(sorted(map(str, missing_targets)))
        )
    return errors


def rows_to_dataframes(
    nodes_rows: list[dict], edges_rows: list[dict]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes_df = _normalize_df(nodes_rows, NODE_COLUMNS)
    edges_df = _normalize_df(edges_rows, EDGE_COLUMNS)
    return nodes_df, edges_df


def save_data(path: Path, nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        nodes_df.to_excel(writer, sheet_name="nodes", index=False)
        edges_df.to_excel(writer, sheet_name="edges", index=False)


def export_data(
    exports_dir: Path, nodes_df: pd.DataFrame, edges_df: pd.DataFrame
) -> dict[str, Path]:
    exports_dir.mkdir(parents=True, exist_ok=True)
    nodes_csv = exports_dir / "nodes.csv"
    edges_csv = exports_dir / "edges.csv"
    gexf_path = exports_dir / "graph.gexf"

    nodes_df.to_csv(nodes_csv, index=False)
    edges_df.to_csv(edges_csv, index=False)

    graph = nx.Graph()
    for _, row in nodes_df.iterrows():
        graph.add_node(
            row["id"],
            label=row["label"],
            type=row["type"],
            description=row["description"],
        )
    for _, row in edges_df.iterrows():
        graph.add_edge(
            row["source"],
            row["target"],
            relationship_type=row["relationship_type"],
            description=row["description"],
        )
    nx.write_gexf(graph, gexf_path)
    return {"nodes": nodes_csv, "edges": edges_csv, "gexf": gexf_path}
