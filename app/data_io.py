from __future__ import annotations

from pathlib import Path
from typing import Iterable

import networkx as nx
import pandas as pd

NODE_COLUMNS = ["id", "label", "type", "description"]
EDGE_COLUMNS = ["source", "target", "relationship_type", "description"]


def _validate_required_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"{label} sheet is missing required columns: {', '.join(missing)}."
        )


def _reorder_columns(df: pd.DataFrame, required: list[str]) -> pd.DataFrame:
    extra_cols = [column for column in df.columns if column not in required]
    return df[required + extra_cols]


def load_data(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes_df = pd.read_excel(path, sheet_name="nodes")
    edges_df = pd.read_excel(path, sheet_name="edges")
    _validate_required_columns(nodes_df, NODE_COLUMNS, "Nodes")
    _validate_required_columns(edges_df, EDGE_COLUMNS, "Edges")
    nodes_df = _reorder_columns(nodes_df, NODE_COLUMNS).fillna("")
    edges_df = _reorder_columns(edges_df, EDGE_COLUMNS).fillna("")
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


def _empty_row_indices(df: pd.DataFrame, columns: list[str]) -> list[int]:
    trimmed = (
        df[columns]
        .applymap(lambda value: str(value).strip())
        .eq("")
        .all(axis=1)
    )
    return df.index[trimmed].tolist()


def validate_data(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing_nodes = [column for column in NODE_COLUMNS if column not in nodes_df.columns]
    if missing_nodes:
        errors.append(
            "Nodes sheet is missing required columns: " + ", ".join(missing_nodes) + "."
        )
    missing_edges = [column for column in EDGE_COLUMNS if column not in edges_df.columns]
    if missing_edges:
        errors.append(
            "Edges sheet is missing required columns: " + ", ".join(missing_edges) + "."
        )
    if errors:
        return errors
    empty_nodes = _empty_row_indices(nodes_df, NODE_COLUMNS)
    empty_edges = _empty_row_indices(edges_df, EDGE_COLUMNS)
    if empty_nodes:
        errors.append(
            "Nodes sheet has completely empty rows at: "
            + ", ".join(str(index + 2) for index in empty_nodes)
            + "."
        )
    if empty_edges:
        errors.append(
            "Edges sheet has completely empty rows at: "
            + ", ".join(str(index + 2) for index in empty_edges)
            + "."
        )
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
    nodes_rows: list[dict],
    edges_rows: list[dict],
    node_columns: list[str],
    edge_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes_df = _normalize_df(nodes_rows, node_columns)
    edges_df = _normalize_df(edges_rows, edge_columns)
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
