from typing import Literal, Optional
from pydantic import BaseModel, Field

GraphMode = Literal[
    "distribution",
    "grouped_mean",
    "entity_timeline",
]

GroupBy = Literal[
    "none",
    "author",
    "document",
    "genre",
    "decade",
]

EntityType = Literal[
    "author",
    "genre",
    "document",
]


class AnalyzeRequest(BaseModel):
    lemma: Optional[str] = None

    metric: str
    metric_min: Optional[float] = None
    metric_max: Optional[float] = None

    authors: list[int] = Field(default_factory=list)
    documents: list[int] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)

    year_from: Optional[int] = None
    year_to: Optional[int] = None

    graph_mode: GraphMode = "distribution"

    # используется только при graph_mode = grouped_mean
    group_by: GroupBy = "none"

    # используется только при graph_mode = entity_timeline
    entity_type: EntityType = "author"


class ChartSelection(BaseModel):
    label: Optional[str] = None

    value: Optional[float] = None
    bin_start: Optional[float] = None
    bin_end: Optional[float] = None

    group: Optional[str] = None
    group_id: Optional[int] = None

    decade: Optional[int] = None

    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    target_value: Optional[float] = None


class ExamplesSummaryRequest(AnalyzeRequest):
    selection: Optional[ChartSelection] = None

    selected_value: Optional[float] = None
    bin_start: Optional[float] = None
    bin_end: Optional[float] = None
    group_value: Optional[str] = None
    decade: Optional[int] = None

    target_value: Optional[float] = None

    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None


class ExamplesRequest(AnalyzeRequest):
    selection: Optional[ChartSelection] = None

    selected_value: Optional[float] = None
    bin_start: Optional[float] = None
    bin_end: Optional[float] = None
    group_value: Optional[str] = None
    decade: Optional[int] = None

    target_value: Optional[float] = None

    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None

    author_id: Optional[int] = None
    limit: int = 10
    offset: int = 0
