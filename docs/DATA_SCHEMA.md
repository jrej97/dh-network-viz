# Data Schema

## Excel Workbook
`data/data.xlsx` contains two worksheets that define the graph.

### nodes sheet
| Column | Type | Description |
| --- | --- | --- |
| id | string | Unique identifier for the node. Required and non-empty. |
| label | string | Human-readable label shown under each node. |
| type | string | Category for icon selection (Person, Place, Institution, Group). |
| description | string | Tooltip and inspector description. |

### edges sheet
| Column | Type | Description |
| --- | --- | --- |
| source | string | Node id that starts the edge. Must exist in nodes.id. |
| target | string | Node id that ends the edge. Must exist in nodes.id. |
| relationship_type | string | Short label describing the relationship. |
| description | string | Additional detail shown in the inspector. |

## Validation Rules
- `nodes.id` values are unique and non-empty.
- Every `edges.source` and `edges.target` value appears in `nodes.id`.
