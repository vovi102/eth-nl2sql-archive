"""Static safety checks for generated GoogleSQL (ported from luanvan `sql_safety.py`)."""

from __future__ import annotations

from sqlglot import Dialect, exp, parse
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope
from sqlglot.tokens import TokenType

PROJECT_DATASET = "nl2sparql-thesis.nl2sparql_analytics"
MANAGED_NAMES = frozenset(
    {
        "block_facts",
        "contract_dimension",
        "entity_labels_v1",
        "labeled_token_transfers",
        "labeled_transactions",
        "token_dimension",
        "token_transfer_facts",
        "transaction_facts",
    }
)
MANAGED_RELATIONS = frozenset(f"{PROJECT_DATASET}.{name}" for name in MANAGED_NAMES)


class ValidationError(ValueError):
    """Raised when SQL is not a single safe read-only query over managed relations.

    ``code`` is ``parse_error`` for unparsable SQL and ``unsafe`` otherwise.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def relation_name(table: exp.Table) -> str:
    """Return the casefolded relation name for tables and table-valued functions.

    SQLGlot keeps a backtick-quoted TVF name such as
    `` `p.d.transaction_facts`(...) `` as one dotted ``Anonymous`` name.
    """
    parts = [table.catalog, table.db]
    parts.append(table.this.name if isinstance(table.this, exp.Anonymous) else table.name)
    return ".".join(part for part in parts if part).casefold()


def _is_cte_reference(table: exp.Table, cte_names: frozenset[str]) -> bool:
    return (
        isinstance(table.this, exp.Identifier)
        and not table.catalog
        and not table.db
        and table.name.casefold() in cte_names
    )


def _has_projected_wildcard(expression: exp.Expression) -> bool:
    for select in expression.find_all(exp.Select):
        for projection in select.expressions:
            unaliased = projection.this if isinstance(projection, exp.Alias) else projection
            if isinstance(unaliased, exp.Star) or (
                isinstance(unaliased, exp.Column) and isinstance(unaliased.this, exp.Star)
            ):
                return True
    return False


def parse_query(sql: str) -> exp.Query:
    """Parse exactly one read-only GoogleSQL query or raise ``ValidationError``."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValidationError("parse_error", "SQL must not be empty")
    try:
        tokens = Dialect.get_or_raise("bigquery").tokenizer_class().tokenize(sql)
        if any(token.comments for token in tokens):
            raise ValidationError("unsafe", "SQL must be one statement without comments")
        if any(token.token_type is TokenType.SEMICOLON for token in tokens):
            raise ValidationError("unsafe", "SQL must be one statement without semicolons")
        expressions = parse(sql, read="bigquery")
    except SqlglotError as exc:
        raise ValidationError("parse_error", f"invalid GoogleSQL: {exc}") from exc
    if len(expressions) != 1 or expressions[0] is None:
        raise ValidationError("unsafe", "SQL must contain exactly one statement")
    expression = expressions[0]
    if not isinstance(expression, exp.Query):
        raise ValidationError("unsafe", "SQL must be a read-only query")
    return expression


def validate_sql(sql: str) -> exp.Query:
    """Validate one read-only query against the managed-relation allowlist."""
    expression = parse_query(sql)
    if _has_projected_wildcard(expression):
        raise ValidationError("unsafe", "SQL must project explicit columns")
    relation_count = 0
    for scope in traverse_scope(expression):
        cte_names = frozenset(name.casefold() for name in scope.cte_sources)
        if scope.udtfs:
            raise ValidationError("unsafe", "SQL must not use table-generating functions")
        for table in scope.tables:
            if _is_cte_reference(table, cte_names):
                continue
            relation_count += 1
            relation = relation_name(table)
            if relation not in MANAGED_RELATIONS:
                raise ValidationError(
                    "unsafe", f"SQL must use managed analytical objects, got {relation!r}"
                )
    if relation_count == 0:
        raise ValidationError("unsafe", "SQL must use at least one managed analytical object")
    return expression
