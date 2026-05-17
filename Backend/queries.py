from sqlalchemy.engine import Connection
from sqlalchemy import (
    select,
    func,
    distinct,
    and_,
    true,
    Integer,
    Float,
    Numeric,
    literal,
)

from db import metadata

EXCLUDED_METRIC_COLUMNS = {
    "sentence_id",
    "id",
}

METRIC_LABELS = {
    "sent_len_no_punct": "Длина предложения без пунктуации",
    "mean_dep_len": "Средняя длина зависимости",
    "max_dep_len": "Максимальная длина зависимости",
    "tree_depth_max": "Максимальная глубина дерева",
    "tree_depth_mean": "Средняя глубина токенов",
    "root_degree": "Степень корня",
    "ratio_nsubj": "Доля субъектных связей",
    "ratio_obj": "Доля объектных связей",
    "ratio_obl": "Доля обстоятельственных зависимостей",
    "ratio_amod_nmod": "Доля определительных связей",
    "ratio_advmod": "Доля наречных модификаторов",
    "ratio_subord_clauses": "Доля подчинительных клауз",
    "ratio_relcl": "Доля относительных придаточных",
    "ratio_conj": "Доля координации",
    "ratio_appos": "Доля аппозиций",
}

FULL_CORPUS_AUTHORS_COUNT = 109
FULL_CORPUS_DOCUMENTS_COUNT = 538

FULL_YEAR_FROM = 1833
FULL_YEAR_TO = 2025


def get_tables():
    return {
        "authors": metadata.tables["authors"],
        "documents": metadata.tables["documents"],
        "sentences": metadata.tables["sentences"],
        "tokens": metadata.tables["tokens"],
        "sentence_metrics": metadata.tables["sentence_metrics"],
        "document_metrics": metadata.tables["document_metrics"],
    }


def normalize_year_filters(params):
    year_from = params.year_from
    year_to = params.year_to

    if year_from == FULL_YEAR_FROM and year_to == FULL_YEAR_TO:
        return None, None

    return year_from, year_to


def get_graph_mode(params) -> str:
    graph_mode = getattr(params, "graph_mode", None)

    if graph_mode:
        return graph_mode

    if getattr(params, "group_by", "none") == "none":
        return "distribution"

    return "grouped_mean"


def get_available_metrics() -> list[dict]:
    tables = get_tables()
    sentence_metrics = tables["sentence_metrics"]

    metrics = []

    for column in sentence_metrics.c:
        if column.name in EXCLUDED_METRIC_COLUMNS:
            continue

        if not isinstance(column.type, (Integer, Float, Numeric)):
            continue

        metrics.append(
            {
                "name": column.name,
                "label": METRIC_LABELS.get(column.name, column.name),
            }
        )

    return metrics


def validate_metric(metric_name: str):
    tables = get_tables()
    sentence_metrics = tables["sentence_metrics"]

    if metric_name not in sentence_metrics.c:
        raise ValueError(f"Unknown metric: {metric_name}")

    if metric_name in EXCLUDED_METRIC_COLUMNS:
        raise ValueError(f"Column is not a metric: {metric_name}")

    column = sentence_metrics.c[metric_name]

    if not isinstance(column.type, (Integer, Float, Numeric)):
        raise ValueError(f"Column is not numeric: {metric_name}")

    return column


def validate_document_metric(metric_name: str):
    tables = get_tables()
    document_metrics = tables["document_metrics"]

    if metric_name not in document_metrics.c:
        raise ValueError(f"Metric {metric_name} not found in document_metrics")

    excluded = {
        "doc_id",
        "document_id",
        "sentence_count",
        "sentences_count",
        "n_sentences",
    }

    if metric_name in excluded:
        raise ValueError(f"Column is not a metric: {metric_name}")

    column = document_metrics.c[metric_name]

    if not isinstance(column.type, (Integer, Float, Numeric)):
        raise ValueError(f"Column is not numeric: {metric_name}")

    return column


def get_document_length_column():
    tables = get_tables()
    document_metrics = tables["document_metrics"]

    for column_name in ["sentence_count", "sentences_count", "n_sentences"]:
        if column_name in document_metrics.c:
            return document_metrics.c[column_name]

    raise ValueError(
        "Не найдена колонка с числом предложений в document_metrics. "
        "Ожидалось одно из названий: sentence_count, sentences_count, n_sentences."
    )


def get_sentence_text_column():
    tables = get_tables()
    sentences = tables["sentences"]

    for column_name in ["text", "sentence_text", "sent_text"]:
        if column_name in sentences.c:
            return sentences.c[column_name]

    raise ValueError(
        "Не найдена колонка с текстом предложения. "
        "Проверь название колонки в таблице sentences."
    )


def has_no_filters(params) -> bool:
    year_from, year_to = normalize_year_filters(params)

    return (
            not params.lemma
            and params.metric_min is None
            and params.metric_max is None
            and not params.authors
            and not params.documents
            and not params.genres
            and year_from is None
            and year_to is None
    )


def resolve_chart_type(group_by: str) -> str:
    if group_by == "none":
        return "histogram"

    if group_by in {"author", "document", "genre"}:
        return "bar"

    if group_by == "decade":
        return "line"

    raise ValueError(f"Unsupported group_by: {group_by}")


def is_integer_metric(metric_name: str) -> bool:
    tables = get_tables()
    column = tables["sentence_metrics"].c[metric_name]
    return isinstance(column.type, Integer)


def base_has_author_doc_columns(base) -> bool:
    return "author_id" in base.c and "doc_id" in base.c


def build_analysis_query(params):
    tables = get_tables()
    year_from, year_to = normalize_year_filters(params)
    graph_mode = get_graph_mode(params)

    metric_column = validate_metric(params.metric)

    sentence_metrics = tables["sentence_metrics"]
    sentences = tables["sentences"]
    documents = tables["documents"]
    authors = tables["authors"]
    tokens = tables["tokens"]

    stmt = (
        select(
            sentence_metrics.c.sentence_id,
            metric_column.label("metric_value"),
        )
        .select_from(sentence_metrics)
    )

    conditions = [metric_column.is_not(None)]

    need_sentences = False
    need_documents = False
    need_authors = False

    needs_metadata_for_summary = not has_no_filters(params)

    if graph_mode == "entity_timeline":
        needs_metadata_for_summary = True

    if params.group_by in {"author", "document", "genre", "decade"}:
        needs_metadata_for_summary = True

    if needs_metadata_for_summary:
        need_sentences = True
        need_documents = True
        need_authors = True

    if params.lemma:
        need_sentences = True

    if need_sentences:
        stmt = stmt.join(
            sentences,
            sentence_metrics.c.sentence_id == sentences.c.sentence_id,
        )

    if need_documents:
        stmt = stmt.join(
            documents,
            sentences.c.doc_id == documents.c.doc_id,
        ).add_columns(
            documents.c.doc_id,
            documents.c.title,
            documents.c.year,
            documents.c.genre,
        )

    if need_authors:
        stmt = stmt.join(
            authors,
            documents.c.author_id == authors.c.author_id,
        ).add_columns(
            authors.c.author_id,
            authors.c.author_name,
        )

    if params.lemma:
        conditions.append(
            select(tokens.c.sentence_id)
            .where(
                tokens.c.sentence_id == sentences.c.sentence_id,
                tokens.c.lemma == params.lemma,
            )
            .exists()
        )

    if params.metric_min is not None:
        conditions.append(metric_column >= params.metric_min)

    if params.metric_max is not None:
        conditions.append(metric_column <= params.metric_max)

    if params.authors:
        conditions.append(documents.c.author_id.in_(params.authors))

    if params.documents:
        conditions.append(documents.c.doc_id.in_(params.documents))

    if params.genres:
        conditions.append(documents.c.genre.in_(params.genres))

    if year_from is not None:
        conditions.append(documents.c.year >= year_from)

    if year_to is not None:
        conditions.append(documents.c.year <= year_to)

    stmt = stmt.where(and_(*conditions))

    return stmt.subquery("base")


def build_examples_query(params):
    tables = get_tables()
    year_from, year_to = normalize_year_filters(params)

    metric_column = validate_metric(params.metric)

    sentence_metrics = tables["sentence_metrics"]
    sentences = tables["sentences"]
    documents = tables["documents"]
    authors = tables["authors"]
    tokens = tables["tokens"]

    sentence_text_col = get_sentence_text_column()

    stmt = (
        select(
            sentences.c.sentence_id,
            documents.c.doc_id,
            documents.c.title,
            documents.c.year,
            documents.c.genre,
            authors.c.author_id,
            authors.c.author_name,
            metric_column.label("metric_value"),
            sentence_text_col.label("sentence_text"),
        )
        .select_from(
            sentence_metrics
            .join(sentences, sentence_metrics.c.sentence_id == sentences.c.sentence_id)
            .join(documents, sentences.c.doc_id == documents.c.doc_id)
            .join(authors, documents.c.author_id == authors.c.author_id)
        )
    )

    conditions = [metric_column.is_not(None)]

    if params.metric_min is not None:
        conditions.append(metric_column >= params.metric_min)

    if params.metric_max is not None:
        conditions.append(metric_column <= params.metric_max)

    if params.authors:
        conditions.append(authors.c.author_id.in_(params.authors))

    if params.documents:
        conditions.append(documents.c.doc_id.in_(params.documents))

    if params.genres:
        conditions.append(documents.c.genre.in_(params.genres))

    if year_from is not None:
        conditions.append(documents.c.year >= year_from)

    if year_to is not None:
        conditions.append(documents.c.year <= year_to)

    if params.lemma:
        conditions.append(
            select(tokens.c.sentence_id)
            .where(
                tokens.c.sentence_id == sentences.c.sentence_id,
                tokens.c.lemma == params.lemma,
            )
            .exists()
        )

    stmt = stmt.where(and_(*conditions))

    return stmt.subquery("base")


def build_document_base_query(params):
    tables = get_tables()
    year_from, year_to = normalize_year_filters(params)

    documents = tables["documents"]
    authors = tables["authors"]
    document_metrics = tables["document_metrics"]

    metric_column = validate_document_metric(params.metric)
    length_column = get_document_length_column()

    stmt = (
        select(
            documents.c.doc_id,
            documents.c.title,
            documents.c.year,
            documents.c.genre,
            authors.c.author_id,
            authors.c.author_name,
            metric_column.label("metric_value"),
            length_column.label("sentence_count"),
        )
        .select_from(
            documents
            .join(document_metrics, documents.c.doc_id == document_metrics.c.doc_id)
            .join(authors, documents.c.author_id == authors.c.author_id)
        )
    )

    conditions = [
        metric_column.is_not(None),
        length_column.is_not(None),
        length_column > 0,
    ]

    if params.metric_min is not None:
        conditions.append(metric_column >= params.metric_min)

    if params.metric_max is not None:
        conditions.append(metric_column <= params.metric_max)

    if params.authors:
        conditions.append(documents.c.author_id.in_(params.authors))

    if params.documents:
        conditions.append(documents.c.doc_id.in_(params.documents))

    if params.genres:
        conditions.append(documents.c.genre.in_(params.genres))

    if year_from is not None:
        conditions.append(documents.c.year >= year_from)

    if year_to is not None:
        conditions.append(documents.c.year <= year_to)

    stmt = stmt.where(and_(*conditions))

    return stmt.subquery("document_base")


def get_summary(conn: Connection, base, use_fixed_counts: bool = False):
    if use_fixed_counts:
        result = conn.execute(
            select(
                func.count(base.c.sentence_id).label("sentences_count"),
                func.avg(base.c.metric_value).label("mean"),
                func.percentile_cont(0.5).within_group(base.c.metric_value).label("median"),
                func.min(base.c.metric_value).label("min"),
                func.max(base.c.metric_value).label("max"),
            )
            .select_from(base)
        ).mappings().one()

        summary = dict(result)
        summary["authors_count"] = FULL_CORPUS_AUTHORS_COUNT
        summary["documents_count"] = FULL_CORPUS_DOCUMENTS_COUNT
        return summary

    if not base_has_author_doc_columns(base):
        raise ValueError(
            "Cannot calculate authors_count/documents_count: "
            "base query does not contain author_id and doc_id. "
            "Check build_analysis_query()."
        )

    result = conn.execute(
        select(
            func.count(base.c.sentence_id).label("sentences_count"),
            func.count(distinct(base.c.author_id)).label("authors_count"),
            func.count(distinct(base.c.doc_id)).label("documents_count"),
            func.avg(base.c.metric_value).label("mean"),
            func.percentile_cont(0.5).within_group(base.c.metric_value).label("median"),
            func.min(base.c.metric_value).label("min"),
            func.max(base.c.metric_value).label("max"),
        )
        .select_from(base)
    ).mappings().one()

    return dict(result)


def weighted_mean_expr(base):
    return (
            func.sum(base.c.metric_value * base.c.sentence_count)
            / func.nullif(func.sum(base.c.sentence_count), 0)
    )


def get_document_summary(conn: Connection, base):
    result = conn.execute(
        select(
            func.coalesce(func.sum(base.c.sentence_count), 0).label("sentences_count"),
            func.count(distinct(base.c.author_id)).label("authors_count"),
            func.count(distinct(base.c.doc_id)).label("documents_count"),
            weighted_mean_expr(base).label("mean"),
            func.percentile_cont(0.5).within_group(base.c.metric_value).label("median"),
            func.min(base.c.metric_value).label("min"),
            func.max(base.c.metric_value).label("max"),
        )
        .select_from(base)
    ).mappings().one()

    return dict(result)


def analyze_histogram(conn: Connection, base, metric_name: str):
    if is_integer_metric(metric_name):
        rows = conn.execute(
            select(
                base.c.metric_value.label("value"),
                func.count().label("count"),
            )
            .select_from(base)
            .where(base.c.metric_value.is_not(None))
            .group_by(base.c.metric_value)
            .order_by(base.c.metric_value)
        ).mappings().all()

        return [
            {
                "label": str(int(row["value"])),
                "value": int(row["value"]),
                "count": row["count"],
            }
            for row in rows
        ]

    bins_count = 20

    min_value, max_value = conn.execute(
        select(
            func.min(base.c.metric_value),
            func.max(base.c.metric_value),
        )
        .select_from(base)
        .where(base.c.metric_value.is_not(None))
    ).one()

    if min_value is None or max_value is None:
        return []

    min_value = float(min_value)
    max_value = float(max_value)

    if min_value == max_value:
        total_count = conn.execute(
            select(func.count())
            .select_from(base)
            .where(base.c.metric_value.is_not(None))
        ).scalar_one()

        return [
            {
                "label": f"{min_value:.2f}",
                "bin_start": min_value,
                "bin_end": max_value,
                "count": total_count,
            }
        ]

    raw_bucket = func.width_bucket(
        base.c.metric_value,
        min_value,
        max_value,
        bins_count,
    )

    bucket = func.least(raw_bucket, bins_count)

    rows = conn.execute(
        select(
            bucket.label("bucket"),
            func.count().label("count"),
        )
        .select_from(base)
        .where(base.c.metric_value.is_not(None))
        .group_by(bucket)
        .order_by(bucket)
    ).mappings().all()

    step = (max_value - min_value) / bins_count

    data = []

    for row in rows:
        bucket_number = int(row["bucket"])

        bin_start = min_value + (bucket_number - 1) * step
        bin_end = bin_start + step

        if bucket_number == bins_count:
            bin_end = max_value

        data.append(
            {
                "label": f"{bin_start:.2f}–{bin_end:.2f}",
                "bin_start": bin_start,
                "bin_end": bin_end,
                "count": row["count"],
            }
        )

    return data


def analyze_bar(conn: Connection, base, group_by: str):
    if group_by == "author":
        group_id_column = base.c.author_id
        group_column = base.c.author_name

        rows = conn.execute(
            select(
                group_id_column.label("group_id"),
                group_column.label("group"),
                func.avg(base.c.metric_value).label("mean"),
                func.count().label("count"),
                func.min(base.c.year).label("year_min"),
                func.max(base.c.year).label("year_max"),
            )
            .select_from(base)
            .group_by(group_id_column, group_column)
            .order_by(func.count().desc())
        ).mappings().all()

        return list(rows)

    if group_by == "document":
        group_id_column = base.c.doc_id
        group_column = base.c.title

        rows = conn.execute(
            select(
                group_id_column.label("group_id"),
                group_column.label("group"),
                func.avg(base.c.metric_value).label("mean"),
                func.count().label("count"),
                func.min(base.c.year).label("year_min"),
                func.max(base.c.year).label("year_max"),
            )
            .select_from(base)
            .group_by(group_id_column, group_column)
            .order_by(func.count().desc())
        ).mappings().all()

        return list(rows)

    if group_by == "genre":
        group_column = base.c.genre

        rows = conn.execute(
            select(
                group_column.label("group"),
                func.avg(base.c.metric_value).label("mean"),
                func.count().label("count"),
                func.min(base.c.year).label("year_min"),
                func.max(base.c.year).label("year_max"),
            )
            .select_from(base)
            .group_by(group_column)
            .order_by(func.count().desc())
        ).mappings().all()

        return list(rows)

    raise ValueError(f"Unsupported bar group_by: {group_by}")


def analyze_line(conn: Connection, base):
    decade = (func.floor(base.c.year / 10) * 10).label("decade")

    rows = conn.execute(
        select(
            decade,
            func.avg(base.c.metric_value).label("mean"),
            func.count().label("count"),
        )
        .select_from(base)
        .where(base.c.year.is_not(None))
        .group_by(decade)
        .order_by(decade)
    ).mappings().all()

    return [
        {
            "period": f"{int(row['decade'])}-е",
            "decade": int(row["decade"]),
            "mean": row["mean"],
            "count": row["count"],
        }
        for row in rows
    ]


def analyze_document_grouped(conn: Connection, base, group_by: str):
    if group_by == "author":
        rows = conn.execute(
            select(
                base.c.author_id.label("group_id"),
                base.c.author_name.label("group"),
                weighted_mean_expr(base).label("mean"),
                func.sum(base.c.sentence_count).label("count"),
                func.count(distinct(base.c.doc_id)).label("documents_count"),
                func.min(base.c.year).label("year_min"),
                func.max(base.c.year).label("year_max"),
            )
            .select_from(base)
            .group_by(base.c.author_id, base.c.author_name)
            .order_by(func.sum(base.c.sentence_count).desc())
        ).mappings().all()

        return "bar", list(rows)

    if group_by == "genre":
        rows = conn.execute(
            select(
                base.c.genre.label("group"),
                weighted_mean_expr(base).label("mean"),
                func.sum(base.c.sentence_count).label("count"),
                func.count(distinct(base.c.doc_id)).label("documents_count"),
                func.min(base.c.year).label("year_min"),
                func.max(base.c.year).label("year_max"),
            )
            .select_from(base)
            .group_by(base.c.genre)
            .order_by(func.sum(base.c.sentence_count).desc())
        ).mappings().all()

        return "bar", list(rows)

    if group_by == "document":
        rows = conn.execute(
            select(
                base.c.doc_id.label("group_id"),
                base.c.title.label("group"),
                base.c.metric_value.label("mean"),
                base.c.sentence_count.label("count"),
                base.c.year.label("year_min"),
                base.c.year.label("year_max"),
            )
            .select_from(base)
            .order_by(base.c.sentence_count.desc())
        ).mappings().all()

        return "bar", list(rows)

    if group_by == "decade":
        decade = (func.floor(base.c.year / 10) * 10).label("decade")

        rows = conn.execute(
            select(
                decade,
                weighted_mean_expr(base).label("mean"),
                func.sum(base.c.sentence_count).label("count"),
                func.count(distinct(base.c.doc_id)).label("documents_count"),
            )
            .select_from(base)
            .where(base.c.year.is_not(None))
            .group_by(decade)
            .order_by(decade)
        ).mappings().all()

        data = [
            {
                "period": f"{int(row['decade'])}-е",
                "decade": int(row["decade"]),
                "mean": row["mean"],
                "count": row["count"],
                "documents_count": row["documents_count"],
            }
            for row in rows
        ]

        return "line", data

    raise ValueError(f"Unsupported document_metrics group_by: {group_by}")


def entity_mean_expr(base):
    if "sentence_count" in base.c:
        return weighted_mean_expr(base)

    return func.avg(base.c.metric_value)


def entity_count_expr(base):
    if "sentence_id" in base.c:
        return func.count(base.c.sentence_id)

    return func.count(base.c.doc_id)


def analyze_entity_timeline(conn: Connection, params):
    if params.lemma:
        base = build_analysis_query(params)
        summary = get_summary(conn, base)
        source = "sentence_metrics"
    else:
        base = build_document_base_query(params)
        summary = get_document_summary(conn, base)
        source = "document_metrics"

    line = analyze_entity_timeline_line(conn, base)
    points = analyze_entity_timeline_points(conn, base, params.entity_type)

    return {
        "chart_type": "entity_timeline",
        "graph_mode": "entity_timeline",
        "entity_type": params.entity_type,
        "source": source,
        "summary": summary,
        "data": {
            "line": line,
            "points": points,
        },
    }


def analyze_entity_timeline_line(conn: Connection, base):
    decade = (func.floor(base.c.year / 10) * 10).label("decade")

    rows = conn.execute(
        select(
            decade,
            entity_mean_expr(base).label("mean"),
            entity_count_expr(base).label("count"),
            func.count(distinct(base.c.doc_id)).label("documents_count"),
            func.count(distinct(base.c.author_id)).label("authors_count"),
        )
        .select_from(base)
        .where(base.c.year.is_not(None))
        .group_by(decade)
        .order_by(decade)
    ).mappings().all()

    return [
        {
            "decade": int(row["decade"]),
            "period": f"{int(row['decade'])}-е",
            "mean": row["mean"],
            "count": row["count"],
            "documents_count": row["documents_count"],
            "authors_count": row["authors_count"],
        }
        for row in rows
    ]


def analyze_author_points_for_timeline(conn: Connection, base):
    decade = (func.floor(base.c.year / 10) * 10).label("decade")

    author_decades = (
        select(
            base.c.author_id,
            base.c.author_name,
            decade,
            func.count(distinct(base.c.doc_id)).label("documents_in_decade"),
        )
        .select_from(base)
        .where(base.c.year.is_not(None))
        .group_by(base.c.author_id, base.c.author_name, decade)
    ).subquery("author_decades")

    ranked = (
        select(
            author_decades,
            func.row_number()
            .over(
                partition_by=author_decades.c.author_id,
                order_by=[
                    author_decades.c.documents_in_decade.desc(),
                    author_decades.c.decade,
                ],
            )
            .label("rn"),
        )
    ).subquery("ranked_author_decades")

    main_decades = (
        select(ranked)
        .where(ranked.c.rn == 1)
    ).subquery("main_author_decades")

    rows = conn.execute(
        select(
            base.c.author_id.label("entity_id"),
            base.c.author_name.label("entity_name"),
            main_decades.c.decade,
            entity_mean_expr(base).label("mean"),
            entity_count_expr(base).label("count"),
            func.count(distinct(base.c.doc_id)).label("documents_count"),
            func.min(base.c.year).label("year_min"),
            func.max(base.c.year).label("year_max"),
        )
        .select_from(
            base.join(
                main_decades,
                base.c.author_id == main_decades.c.author_id,
            )
        )
        .group_by(
            base.c.author_id,
            base.c.author_name,
            main_decades.c.decade,
        )
        .order_by(main_decades.c.decade, base.c.author_name)
    ).mappings().all()

    return [
        {
            "entity_type": "author",
            "entity_id": row["entity_id"],
            "entity_name": row["entity_name"],
            "decade": int(row["decade"]),
            "period": f"{int(row['decade'])}-е",
            "mean": row["mean"],
            "count": row["count"],
            "documents_count": row["documents_count"],
            "year_min": row["year_min"],
            "year_max": row["year_max"],
        }
        for row in rows
    ]


def analyze_genre_points_for_timeline(conn: Connection, base):
    decade = (func.floor(base.c.year / 10) * 10).label("decade")

    genre_decades = (
        select(
            base.c.genre.label("genre"),
            decade,
            func.count(distinct(base.c.doc_id)).label("documents_in_decade"),
        )
        .select_from(base)
        .where(
            base.c.year.is_not(None),
            base.c.genre.is_not(None),
        )
        .group_by(base.c.genre, decade)
    ).subquery("genre_decades")

    ranked = (
        select(
            genre_decades,
            func.row_number()
            .over(
                partition_by=genre_decades.c.genre,
                order_by=[
                    genre_decades.c.documents_in_decade.desc(),
                    genre_decades.c.decade,
                ],
            )
            .label("rn"),
        )
    ).subquery("ranked_genre_decades")

    main_decades = (
        select(ranked)
        .where(ranked.c.rn == 1)
    ).subquery("main_genre_decades")

    rows = conn.execute(
        select(
            base.c.genre.label("entity_name"),
            main_decades.c.decade,
            entity_mean_expr(base).label("mean"),
            entity_count_expr(base).label("count"),
            func.count(distinct(base.c.doc_id)).label("documents_count"),
            func.count(distinct(base.c.author_id)).label("authors_count"),
            func.min(base.c.year).label("year_min"),
            func.max(base.c.year).label("year_max"),
        )
        .select_from(
            base.join(
                main_decades,
                base.c.genre == main_decades.c.genre,
            )
        )
        .where(base.c.genre.is_not(None))
        .group_by(
            base.c.genre,
            main_decades.c.decade,
        )
        .order_by(main_decades.c.decade, base.c.genre)
    ).mappings().all()

    return [
        {
            "entity_type": "genre",
            "entity_id": None,
            "entity_name": row["entity_name"],
            "decade": int(row["decade"]),
            "period": f"{int(row['decade'])}-е",
            "mean": row["mean"],
            "count": row["count"],
            "documents_count": row["documents_count"],
            "authors_count": row["authors_count"],
            "year_min": row["year_min"],
            "year_max": row["year_max"],
        }
        for row in rows
    ]


def analyze_document_points_for_timeline(conn: Connection, base):
    decade = (func.floor(base.c.year / 10) * 10).label("decade")

    rows = conn.execute(
        select(
            base.c.doc_id.label("entity_id"),
            base.c.title.label("entity_name"),
            base.c.author_name,
            base.c.genre,
            decade,
            entity_mean_expr(base).label("mean"),
            entity_count_expr(base).label("count"),
            func.min(base.c.year).label("year_min"),
            func.max(base.c.year).label("year_max"),
        )
        .select_from(base)
        .where(base.c.year.is_not(None))
        .group_by(
            base.c.doc_id,
            base.c.title,
            base.c.author_name,
            base.c.genre,
            decade,
        )
        .order_by(decade, base.c.author_name, base.c.title)
        .limit(300)
    ).mappings().all()

    return [
        {
            "entity_type": "document",
            "entity_id": row["entity_id"],
            "entity_name": row["entity_name"],
            "author_name": row["author_name"],
            "genre": row["genre"],
            "decade": int(row["decade"]),
            "period": f"{int(row['decade'])}-е",
            "mean": row["mean"],
            "count": row["count"],
            "documents_count": 1,
            "year_min": row["year_min"],
            "year_max": row["year_max"],
        }
        for row in rows
    ]


def analyze_entity_timeline_points(conn: Connection, base, entity_type: str):
    if entity_type == "author":
        return analyze_author_points_for_timeline(conn, base)

    if entity_type == "genre":
        return analyze_genre_points_for_timeline(conn, base)

    if entity_type == "document":
        return analyze_document_points_for_timeline(conn, base)

    raise ValueError(f"Unsupported entity_type: {entity_type}")


def get_selection_conditions(base, params):
    conditions = []

    selection = getattr(params, "selection", None)

    selected_value = getattr(params, "selected_value", None)
    bin_start = getattr(params, "bin_start", None)
    bin_end = getattr(params, "bin_end", None)
    group_value = getattr(params, "group_value", None)
    decade = getattr(params, "decade", None)

    if selection:
        selected_value = selected_value if selected_value is not None else selection.value
        bin_start = bin_start if bin_start is not None else selection.bin_start
        bin_end = bin_end if bin_end is not None else selection.bin_end
        group_value = group_value if group_value is not None else selection.group
        decade = decade if decade is not None else selection.decade

    if get_graph_mode(params) == "entity_timeline":
        entity_type = getattr(params, "entity_type", None)
        entity_id = getattr(params, "entity_id", None)
        entity_name = getattr(params, "entity_name", None)

        if selection:
            entity_type = entity_type or selection.entity_type
            entity_id = entity_id if entity_id is not None else selection.entity_id
            entity_name = entity_name or selection.entity_name
            decade = decade if decade is not None else selection.decade

        if decade is not None:
            conditions.append(base.c.year >= decade)
            conditions.append(base.c.year < decade + 10)

        if entity_type == "author":
            if entity_id is not None:
                conditions.append(base.c.author_id == entity_id)
            elif entity_name:
                conditions.append(base.c.author_name == entity_name)

        elif entity_type == "genre":
            if entity_name:
                conditions.append(base.c.genre == entity_name)

        elif entity_type == "document":
            if entity_id is not None:
                conditions.append(base.c.doc_id == entity_id)
            elif entity_name:
                conditions.append(base.c.title == entity_name)

        return conditions

    if params.group_by == "none":
        if selected_value is not None:
            conditions.append(base.c.metric_value == selected_value)
        elif bin_start is not None and bin_end is not None:
            conditions.append(base.c.metric_value >= bin_start)
            conditions.append(base.c.metric_value <= bin_end)

    elif params.group_by == "genre":
        if group_value:
            conditions.append(base.c.genre == group_value)

    elif params.group_by == "decade":
        if decade is not None:
            conditions.append(base.c.year >= decade)
            conditions.append(base.c.year < decade + 10)

    elif params.group_by == "author":
        group_id = selection.group_id if selection else None

        if group_id is not None:
            conditions.append(base.c.author_id == group_id)
        elif group_value:
            conditions.append(base.c.author_name == group_value)

    elif params.group_by == "document":
        group_id = selection.group_id if selection else None

        if group_id is not None:
            conditions.append(base.c.doc_id == group_id)
        elif group_value:
            conditions.append(base.c.title == group_value)

    return conditions


def get_options(conn: Connection) -> dict:
    tables = get_tables()

    authors = conn.execute(
        select(
            tables["authors"].c.author_id.label("id"),
            tables["authors"].c.author_name.label("name"),
        ).order_by(tables["authors"].c.author_name)
    ).mappings().all()

    documents = conn.execute(
        select(
            tables["documents"].c.doc_id.label("id"),
            tables["documents"].c.title,
            tables["documents"].c.author_id,
            tables["documents"].c.year,
            tables["documents"].c.genre,
        ).order_by(tables["documents"].c.title)
    ).mappings().all()

    genres = conn.execute(
        select(distinct(tables["documents"].c.genre))
        .where(tables["documents"].c.genre.is_not(None))
        .order_by(tables["documents"].c.genre)
    ).scalars().all()

    year_min, year_max = conn.execute(
        select(
            func.min(tables["documents"].c.year),
            func.max(tables["documents"].c.year),
        )
    ).one()

    return {
        "authors": list(authors),
        "documents": list(documents),
        "genres": genres,
        "metrics": get_available_metrics(),
        "year_min": year_min,
        "year_max": year_max,
        "group_by_options": [
            {"name": "none", "label": "Не группировать"},
            {"name": "author", "label": "Автор"},
            {"name": "document", "label": "Произведение"},
            {"name": "genre", "label": "Жанр"},
            {"name": "decade", "label": "Десятилетие"},
        ],
        "graph_mode_options": [
            {"name": "distribution", "label": "Распределение"},
            {"name": "grouped_mean", "label": "Средние по группам"},
            {"name": "entity_timeline", "label": "Объекты во времени"},
        ],
        "entity_type_options": [
            {"name": "author", "label": "Авторы"},
            {"name": "genre", "label": "Жанры"},
            {"name": "document", "label": "Произведения"},
        ],
    }


def get_examples_summary(conn: Connection, params):
    base = build_examples_query(params)
    conditions = get_selection_conditions(base, params)

    stmt = (
        select(
            base.c.author_id,
            base.c.author_name,
            func.count().label("count"),
            func.min(base.c.year).label("year_min"),
            func.max(base.c.year).label("year_max"),
            func.avg(base.c.metric_value).label("mean"),
        )
        .select_from(base)
        .group_by(base.c.author_id, base.c.author_name)
        .order_by(func.count().desc())
    )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    rows = conn.execute(stmt).mappings().all()

    return {
        "items": [
            {
                "author_id": row["author_id"],
                "author_name": row["author_name"],
                "count": row["count"],
                "year_min": row["year_min"],
                "year_max": row["year_max"],
                "mean": row["mean"],
            }
            for row in rows
        ]
    }


def get_examples(conn: Connection, params):
    base = build_examples_query(params)
    conditions = get_selection_conditions(base, params)

    author_id = getattr(params, "author_id", None)

    if author_id is not None:
        conditions.append(base.c.author_id == author_id)

    filtered_stmt = select(base).select_from(base)

    if conditions:
        filtered_stmt = filtered_stmt.where(and_(*conditions))

    filtered = filtered_stmt.subquery("filtered_examples")

    total = conn.execute(
        select(func.count()).select_from(filtered)
    ).scalar_one()

    selection = getattr(params, "selection", None)

    target_value = getattr(params, "target_value", None)

    if target_value is None and selection is not None:
        target_value = getattr(selection, "target_value", None)

    order_by_items = []

    if target_value is not None:
        order_by_items.append(func.abs(filtered.c.metric_value - target_value))

    order_by_items.extend(
        [
            filtered.c.year,
            filtered.c.title,
            filtered.c.sentence_id,
        ]
    )

    rows = conn.execute(
        select(
            filtered.c.sentence_id,
            filtered.c.sentence_text,
            filtered.c.author_name,
            filtered.c.title,
            filtered.c.year,
            filtered.c.genre,
            filtered.c.metric_value,
        )
        .select_from(filtered)
        .order_by(*order_by_items)
        .limit(params.limit)
        .offset(params.offset)
    ).mappings().all()

    return {
        "total": total,
        "limit": params.limit,
        "offset": params.offset,
        "items": [
            {
                "sentence_id": row["sentence_id"],
                "text": row["sentence_text"],
                "author_name": row["author_name"],
                "title": row["title"],
                "year": row["year"],
                "genre": row["genre"],
                "metric_value": row["metric_value"],
            }
            for row in rows
        ],
    }


def analyze(conn: Connection, params):
    graph_mode = get_graph_mode(params)

    if graph_mode == "distribution":
        base = build_analysis_query(params)
        summary = get_summary(
            conn,
            base,
            use_fixed_counts=has_no_filters(params),
        )
        data = analyze_histogram(conn, base, params.metric)

        return {
            "chart_type": "histogram",
            "graph_mode": "distribution",
            "group_by": "none",
            "source": "sentence_metrics",
            "summary": summary,
            "data": data,
        }

    if graph_mode == "grouped_mean":
        if not params.lemma and params.group_by in {"author", "document", "genre", "decade"}:
            base = build_document_base_query(params)
            summary = get_document_summary(conn, base)
            chart_type, data = analyze_document_grouped(conn, base, params.group_by)

            return {
                "chart_type": chart_type,
                "graph_mode": "grouped_mean",
                "group_by": params.group_by,
                "source": "document_metrics",
                "summary": summary,
                "data": data,
            }

        chart_type = resolve_chart_type(params.group_by)

        base = build_analysis_query(params)
        summary = get_summary(
            conn,
            base,
            use_fixed_counts=has_no_filters(params),
        )

        if chart_type == "histogram":
            data = analyze_histogram(conn, base, params.metric)
        elif chart_type == "bar":
            data = analyze_bar(conn, base, params.group_by)
        elif chart_type == "line":
            data = analyze_line(conn, base)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return {
            "chart_type": chart_type,
            "graph_mode": "grouped_mean",
            "group_by": params.group_by,
            "source": "sentence_metrics",
            "summary": summary,
            "data": data,
        }

    if graph_mode == "entity_timeline":
        return analyze_entity_timeline(conn, params)

    raise ValueError(f"Unsupported graph_mode: {graph_mode}")
