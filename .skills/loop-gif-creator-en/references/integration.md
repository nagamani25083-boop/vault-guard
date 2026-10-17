# Runtime integration and validation

For a direct task, author input JSON and run the CLI from the skill root. The CLI refuses to overwrite an existing file. For a generated app, copy assets/runtime.mjs to its source tree and import it; runtime files must be inside the app, not referenced from the skill filesystem. The HTML is a runnable reference, not mandatory product UI.

```sh
node scripts/test.mjs
node scripts/run.mjs assets/example.json result.gif
python3 -m http.server 8765 --directory assets
```

Serve the assets directory over HTTP; opening file:// will block fetch of the example. Use an available port when 8765 is occupied. Test with actual user input, not only this fixture. Adapt the JSON editor into domain-specific controls. Preserve error, loading and result states; invalid input must clear stale download links. Keep original inputs immutable.

For application authoring with a platform model: request structured JSON conforming to the example; validate on return and make model errors visible. Do not eval code or silently replace failed generations with examples. Reuse working PDF/Word/Excel skills only when imports/exports in those formats are requested.

Use HashRouter for generated static web apps unless server fallback is verified. Bind async results to the active request; cancel obsolete work. Keep files as Blob/Uint8Array, never convert binary to text. Test refresh, invalid input, actual download and reopening the downloaded file.

Verification layers: unit contracts; decoded artifact; browser workflow; platform-model integration; QA-generated application; published app. The bundle only records layers actually run in the external verification report.
