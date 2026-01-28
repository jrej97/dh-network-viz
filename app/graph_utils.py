from __future__ import annotations

import pandas as pd

ICON_MAP = {
    "person": "/assets/icons/person.svg",
    "place": "/assets/icons/place.svg",
    "institution": "/assets/icons/institution.svg",
    "group": "/assets/icons/group.svg",
}


def resolve_icon(node_type: str) -> str:
    if not node_type:
        return ICON_MAP["group"]
    return ICON_MAP.get(node_type.strip().lower(), ICON_MAP["group"])


def build_elements(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> list[dict]:
    elements: list[dict] = []
    for _, row in nodes_df.iterrows():
        elements.append(
            {
                "data": {
                    "id": str(row["id"]),
                    "label": str(row["label"]),
                    "type": str(row["type"]),
                    "description": str(row["description"]),
                    "icon": resolve_icon(str(row["type"])),
                }
            }
        )
    for index, row in edges_df.iterrows():
        source = str(row["source"])
        target = str(row["target"])
        elements.append(
            {
                "data": {
                    "id": f"edge-{index}-{source}-{target}",
                    "source": source,
                    "target": target,
                    "relationship_type": str(row["relationship_type"]),
                    "description": str(row["description"]),
                }
            }
        )
    return elements
