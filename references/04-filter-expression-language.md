# Filter Expression Language

## Operators

- `AND` - both conditions must match
- `OR` - at least one condition must match
- `NOT` - negate a condition

## Operator precedence

Default precedence:

1. `NOT`
2. `AND`
3. `OR`

Use parentheses `(` `)` for explicit grouping.

## Terms and phrases

- Unquoted term: `ERROR`
- Quoted phrase: `"database connection failed"`
- Both `'...'` and `"..."` are supported

## Expression examples

- `ERROR AND Kafka`
- `(ERROR OR CRITICAL) AND NOT test`
- `"eventEntity" AND ("MOVE" OR "PLAN" OR "INTERMODAL_UNIT")`

## Regex mode

When `search.regex` is `true` in config JSON, terms are treated as regular expressions.

Example expression: `"ERROR [0-9]{3}"` with `"search": { "expression": "...", "regex": true }`.

## Exact word matching

Set both `search.word_boundary` and `search.strip_quotes` to `true` (same idea as the old `--exact-match` flag).

Useful for JSON/CSV logs and strict token matching.
