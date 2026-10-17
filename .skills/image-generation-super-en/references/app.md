# App Integration

The app calls the existing Edge Functions through the overseas gateway API IDs: generation `api-Aa2P8vvAdWOL` and editing `api-rY7JzWWDg5RL`. The server reads `INTEGRATIONS_API_KEY`; the client never receives the key.

The response is synchronous JSON. Read `data[0].b64_json`, prepend `data:image/png;base64,` for a React Native `<Image>`, and keep Base64 out of logs. For editing, use `expo-image-picker` and `expo-image-manipulator` to produce one MIME-correct image data URL in `images[0].image_url`.

Supported project types: Web, Task, MiniProgram and App. Preserve the existing function names `image-generations` and `image-edits`, and use the raw 27502 image API endpoint.
