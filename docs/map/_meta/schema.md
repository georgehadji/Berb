# Schema

Closed set. Change this file in the same commit as any practice change.

## Node types

| `type:` | Lives at | Template |
|---|---|---|
| object | `objects/<cluster>/<slug>.md` | `_templates/object.md` |
| process | `processes/<slug>.md` | `_templates/process.md` |

## Labels

- `cluster`: one of `pipeline-core`, `llm`, `literature`, `experiment`, `integrity-review`, `config-prompts`, `surfaces`.
- `universe`: `live` | `leftover` | `ghost`.
- `status`: `stub` | `verified` | `stale`. `verified` requires a date, a commit, and `path:line` citations.
- `entity`: path of the owning source file or package.

## Naming

Slugs are kebab-case. Cards named for the code entity, with the product word in the first sentence if different.
