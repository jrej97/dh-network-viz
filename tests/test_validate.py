from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))

from data_io import EDGE_COLUMNS, NODE_COLUMNS, validate_data


def test_validate_missing_columns() -> None:
    nodes_df = pd.DataFrame({"id": ["n1"], "label": ["Node 1"]})
    edges_df = pd.DataFrame({"source": ["n1"], "target": ["n2"]})
    errors = validate_data(nodes_df, edges_df)
    assert any("Nodes sheet is missing required columns" in error for error in errors)
    assert any("Edges sheet is missing required columns" in error for error in errors)


def test_validate_empty_rows() -> None:
    nodes_df = pd.DataFrame(
        [
            {"id": "n1", "label": "Node 1", "type": "Person", "description": ""},
            {"id": "", "label": "", "type": "", "description": ""},
        ]
    )[NODE_COLUMNS]
    edges_df = pd.DataFrame(
        [
            {
                "source": "n1",
                "target": "n2",
                "relationship_type": "knows",
                "description": "",
            },
            {"source": "", "target": "", "relationship_type": "", "description": ""},
        ]
    )[EDGE_COLUMNS]
    errors = validate_data(nodes_df, edges_df)
    assert any("Nodes sheet has completely empty rows" in error for error in errors)
    assert any("Edges sheet has completely empty rows" in error for error in errors)


def test_validate_edge_reference() -> None:
    nodes_df = pd.DataFrame(
        [{"id": "n1", "label": "Node 1", "type": "Person", "description": ""}]
    )[NODE_COLUMNS]
    edges_df = pd.DataFrame(
        [
            {
                "source": "n1",
                "target": "n2",
                "relationship_type": "knows",
                "description": "",
            }
        ]
    )[EDGE_COLUMNS]
    errors = validate_data(nodes_df, edges_df)
    assert any("Edges have missing target ids" in error for error in errors)
