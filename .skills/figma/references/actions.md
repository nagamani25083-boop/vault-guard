# Figma action contract

Read this whole file, in one go, before choosing actions or building their arguments. It contains, in order:

- **Caller defaults**: who may call each action by default, and which reads may be opened to visitors with a `pin` on one file. Every generated Edge Function starts from this table.
- **Rate limits**: why results must be cached in the app's database.
- **Arguments**: every action's arguments and rules.
- **Examples**: turning a link into IDs, reading and rendering frames, extracting tokens, with responses.

## Caller defaults

`references/edge-function.md` step 2 makes every action declare `callers`. Start from the default below. The App owner may open a read further, and the generated application must then say so in its closing summary. `public` requires no login system; opening a file-scoped read needs a `pin` that fixes the target, and the owner's acceptance that the pinned file's structure, tokens and rendered output become public.

| Action | Default | Opening it to `public` |
| --- | --- | --- |
| `get_current_user` | `authenticated` | Keep closed: it exposes the owner's identity. |
| `discover_resources` | `authenticated` | Keep closed: caller-chosen URLs can reach any file the account can open. |
| `list_team_projects` | `authenticated` | Keep closed: it exposes account structure. |
| `list_project_files` | `authenticated` | Keep closed: caller-chosen project IDs reach account structure. |
| `get_file_metadata` | `authenticated` | Only with `pin: { fileKey: "<key>" }` and owner acceptance that the file's name, role and thumbnail become public. |
| `get_file_content` | `authenticated` | Only with `pin: { fileKey: "<key>" }` and owner acceptance that the file's structure becomes public. |
| `get_file_nodes` | `authenticated` | Only with `pin: { fileKey: "<key>" }` and the same owner acceptance. |
| `render_node_images` | `authenticated` | Only with `pin: { fileKey: "<key>", nodeIds: ["<id>"] }`: rendered output becomes public and every call draws on the owner's rate-limit allowance. |
| `get_image_fills` | `authenticated` | Only with `pin: { fileKey: "<key>" }`: image fill URLs become public. |
| `extract_design_tokens` | `authenticated` | Only with `pin: { fileKey: "<key>" }`: the file's tokens become public. |
| `tokens_to_tailwind` | `authenticated` | Keep closed: caller-chosen token payloads only waste quota. |
| `list_file_styles` | `authenticated` | Only with `pin: { fileKey: "<key>" }`. |
| `list_file_components` | `authenticated` | Only with `pin: { fileKey: "<key>" }`. |
| `list_file_component_sets` | `authenticated` | Only with `pin: { fileKey: "<key>" }`. |
| `get_component_detail` | `authenticated` | Keep closed: caller-chosen keys can reach any published item in the org. |
| `get_component_set` | `authenticated` | Keep closed: same reason. |
| `get_style` | `authenticated` | Keep closed: same reason. |
| `list_team_components` | `authenticated` | Keep closed: it exposes the whole published library. |
| `list_team_component_sets` | `authenticated` | Keep closed: same reason. |
| `list_team_styles` | `authenticated` | Keep closed: same reason. |
| `list_prototype_interactions` | `authenticated` | Only with `pin: { fileKey: "<key>" }`: the file's interaction logic becomes public. |

## Rate limits

Figma applies API rate limits per file and per plan, and a file on a free Starter team can be read only a handful of times per month. Cache what an app needs in its own database instead of re-reading on every page view. `CONNECT_RATE_LIMITED` (HTTP 429 through the gateway) means wait for the window to reset — do not retry.

## Arguments

Arguments use the names below; the gateway and `scripts/connect.py` accept nothing else. Every ID is a string: `fileKey` is the base62 key in the file URL (`https://www.figma.com/design/<fileKey>/...`), node IDs look like `"1:2"`, team IDs are digit strings, and component/style `key`s are the published hex keys. The gateway pins every Tool and version, fixes `branch_data` off and `include_variables` off, and returns only the fields listed here.

| Action | Arguments (* required) | Rules |
| --- | --- | --- |
| `get_current_user` | — | The connected Figma account (`id`, `email`, `handle`, `imgUrl`). |
| `discover_resources` | `figmaUrl`, `fileKey`, `nodeDepth`, `teamId`, `projectId` | Resolve a link or IDs to `extractedIds` (`fileKey`, `nodeId`, `teamId`, `projectId`), `nodes`, `files`, `projects`. `figmaUrl` is an `https://*.figma.com` link. |
| `list_team_projects` | `teamId` * | `projects[]` of one team. |
| `list_project_files` | `projectId` * | `files[]` (`key`, `name`, `lastModified`, `thumbnailUrl`) of one project. Branch data stays off. |
| `get_file_metadata` | `fileKey` * | `name`, `url`, `version`, `role`, `editorType`, `folderName`, `linkAccess`, `thumbnailUrl`, `lastTouchedAt`, `creator`, `lastTouchedBy`. |
| `get_file_content` | `fileKey` *, `nodeIds`, `depth`, `geometry` | Simplified file tree in `nodes`. `nodeIds` is a list of 1–50 node IDs joined upstream; `depth` is 1–64; `geometry` is `paths` or absent. |
| `get_file_nodes` | `fileKey` *, `nodeIds` *, `depth`, `geometry` | Same bounds as `get_file_content`; returns `nodes` plus `name`, `version`, `error`. Empty `nodes` is a valid result. |
| `render_node_images` | `fileKey` *, `nodeIds` *, `format`, `scale`, `contentsOnly` | `images` maps node ID to a 30-day render URL. `format` is `png`/`jpg`/`svg`/`pdf`; `scale` is 0.01–4. |
| `get_image_fills` | `fileKey` * | `images` maps fill keys to URLs. |
| `extract_design_tokens` | `fileKey` *, `extractFromNodes`, `includeLocalStyles` | `colors`, `typography`, `spacing`, `shadows`, `borderRadius`, `sources`, `totalTokens`. Variables stay off: they need an Enterprise-only scope. |
| `tokens_to_tailwind` | `tokens` *, `prefix`, `configFormat`, `includeFontImports` | `tokens` is a token object (for example the `extract_design_tokens` output), up to 256 KiB. `configFormat` is `js`/`ts`/`mjs`/`cjs`. Returns `configContent`, `globalsCss`, `tokenSummary`. |
| `list_file_styles` | `fileKey` * | `items[]` of styles used by the file. |
| `list_file_components` | `fileKey` * | `items[]` of components used by the file. |
| `list_file_component_sets` | `fileKey` * | `items[]` of component sets used by the file. |
| `get_component_detail` | `componentKey` * | One published component: `key`, `name`, `description`, `fileKey`, `nodeId`, `containingFrame`, `user`. |
| `get_component_set` | `componentSetKey` * | One published component set with the same fields. |
| `get_style` | `styleKey` * | One published style: adds `styleType` and `sortPosition`. |
| `list_team_components` | `teamId` *, `after`, `before`, `pageSize` | Published components, `pageSize` 1–100 (default 50), `cursor` for the next page. |
| `list_team_component_sets` | `teamId` *, `after`, `before`, `pageSize` | Published component sets, same paging. |
| `list_team_styles` | `teamId` *, `after`, `before`, `pageSize` | Published styles, same paging. |
| `list_prototype_interactions` | `fileKey` *, `analyzeComponents`, `includeAnimations` | `interactions` (`nodeId`, `trigger`, `actions`), `prototypeFlows`, `componentStates`, `animationTypesUsed`, `totalInteractions`. |

## Examples

Turn a pasted link into IDs:

```json
{"action":"discover_resources","arguments":{"figmaUrl":"https://www.figma.com/design/AaBbCcDdEeFfGgHhIiJjKk/My-File?node-id=1-2"}}
```

```json
{"successful":true,"data":{"extractedIds":{"fileKey":"AaBbCcDdEeFfGgHhIiJjKk","nodeId":"1:2"},
 "nodes":[{"id":"1:2","name":"Hero","type":"FRAME"}],"files":[],"projects":[]}}
```

Read a frame subtree and render it:

```json
{"action":"get_file_nodes","arguments":{"fileKey":"AaBbCcDdEeFfGgHhIiJjKk","nodeIds":["1:2"],"depth":4}}
```

```json
{"action":"render_node_images","arguments":{"fileKey":"AaBbCcDdEeFfGgHhIiJjKk","nodeIds":["1:2"],"format":"png","scale":2}}
```

Extract tokens and convert them:

```json
{"action":"extract_design_tokens","arguments":{"fileKey":"AaBbCcDdEeFfGgHhIiJjKk","includeLocalStyles":true}}
```

```json
{"action":"tokens_to_tailwind","arguments":{"tokens":{...},"configFormat":"ts"}}
```
