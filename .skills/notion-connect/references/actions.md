# Notion Action contract

Resource IDs are UUIDs obtained from the owner or a prior result. Property IDs are the exact values returned by the schema. Preserve their encoding. All responses are `successful/data/error`; check the boolean business result as well as HTTP status. Request limit: 64 KiB. Response limit: 1 MiB. No automatic retry or redirect.

| Action | Required | Optional | Returned data |
| --- | --- | --- | --- |
| search | — | query, objectType (`page`, the default, or `database`), cursor | items (page fields; a database item adds `title`), nextCursor, hasMore; title search, not full text |
| get_page | pageId | — | page fields |
| list_block_children | blockId | cursor | items of blocks (`id`, `type`, `parent`, `hasChildren`, `archived` and the typed payload under the `type` key), nextCursor, hasMore |
| get_database | databaseId | — | id, object, title, description, parent, url, properties (schema by name), isInline, inTrash |
| query_database | databaseId | filter, sorts, cursor | items (page fields), nextCursor, hasMore |
| create_page | parentId (a page), title | markdown | page fields |
| add_database_row | databaseId, properties | — | page fields |
| append_blocks | blockId, blocks | after (a sibling block ID) | items of `id`, `type`, `parent`, `hasChildren` |
| update_page_properties | pageId, properties | — | page fields |
| get_page_property | pageId, propertyId | cursor | scalar property item or results, propertyItem, nextCursor, hasMore |

Page fields are `id`, `object`, `url`, `parent`, `properties`, `createdTime`, `lastEditedTime`, `archived` and `inTrash`; the timestamps are camelCase ISO 8601 strings. Text is never a plain string. A page's title is the `title` array of the `properties` entry whose `type` is `title`; that array, a database's `title` and `description`, and every `rich_text` value are arrays of rich-text objects. Display text by joining each element's `plain_text`; do not render these arrays directly. A page has no top-level `title`.

Search indexing is not immediate: a page or database created moments ago may not appear yet. Databases with multiple data sources are not supported and never appear in search. `get_database`, `query_database` or `add_database_row` on one fails with upstream status 400, which the program reports as `RESULT_UNKNOWN`. Do not retry; ask the owner for a database with a single data source.

`add_database_row.properties` is a list of 1–100 `{name, type, value}` objects. `name` and `type` must match the schema from `get_database` exactly; each database has one `title` property and other text is `rich_text`. `value` is always a string: numbers as `"0"`, checkboxes as `"True"` or `"False"`, dates in ISO 8601 (a range as `start/end`), `multi_select`, `people`, `relation` and `files` as comma-separated values. Read-only types such as formula and rollup cannot be written.

`update_page_properties.properties` uses Notion's native typed values keyed by an existing property name or ID. Preserve false, 0, empty strings, and explicit null where the property type supports clearing. Update only the explicitly requested properties; omit unrelated fields.

`create_page` creates a page under another page; use `add_database_row` for a database record. `markdown` is Notion-flavored Markdown for the page body.

`append_blocks.blocks` is a list of 1–100 blocks. Use `{content, block_property}` for text blocks, where `block_property` is `paragraph`, `heading_1`–`heading_3`, `callout`, `to_do`, `toggle`, `quote`, `bulleted_list_item`, `numbered_list_item` or `divider`; content supports inline Markdown. Use a full Notion block such as `{"type": "code", "code": {...}}` for code and tables. To insert after a heading, pass the page as `blockId` and the heading as `after`.

Queries accept Notion filter objects and sort objects; page size is fixed at 100. Limit a UI view to bounded pages and offer an explicit next page; do not silently claim a partial result is complete.

To read nested content, paginate children and recursively expand only blocks whose `hasChildren` is true. Track visited IDs and bound depth/total requests; show a partial indicator when reaching the limit. Page properties may truncate relation, people, title, rich_text or rollup values; paginate get_page_property until `hasMore` is false. Never infer an empty property from a failed request.

## Caller defaults

Every action defaults to authenticated callers with application-specific access checks. Search remains private. The owner may publish a fixed page or database: pin resource IDs server-side and allow only the fields/content they intend to expose. Public create/append forms require a fixed parent, an explicit field whitelist, validation and abuse controls; tell the owner that any visitor can invoke them and consume their allowance. Do not allow public callers to select arbitrary resource IDs or edit existing records.

A relation can reference another resource the connection cannot read; permissions errors are not empty results. Temporary signed file URLs may expire; do not treat them as durable copied assets.
