## Inputs and decisions
- Determine whether to animate the supplied image, use it as inspiration, or draw from scratch. Preserve supplied artwork unless redraw is requested. Compose a platform image skill only for requested AI imagery.
- Convert Canvas RGBA frames with rgbaToIndexed, then call encode. Decode uploaded local images with Blob URLs, use origin-clean canvases and revoke URLs afterward. demoFrames is a smoke-test pattern, not a universal result.
- Design periodic motion with t=i/N; avoid a duplicated endpoint that pauses the loop. Decode exported GIFs and inspect frame count, size, loop, duration and bytes before displaying preview and download.

## Supported scope
- The browser encoder uses a fixed 256-color palette and composites transparency onto white. It does not guarantee transparent GIFs, photographic color accuracy or automatic compliance with platform size limits.
- Dimensions: 16–512 px; 5–30 fps; 2–120 frames; at most 6 million total pixels. Reliability-first encoding may create larger files; reduce dimensions/frame count based on measured target limits. Original Python optimization utilities are retained under scripts/upstream for compatible Python image runtimes.

Each indexed frame is a width*height Uint8Array using a 3-3-2 RGB palette. For uploaded images use createImageBitmap(file), draw to Canvas, then getImageData → rgbaToIndexed → encode. Reduce pixels/frames for size targets and show actual bytes. Python direct tasks can reuse scripts/upstream/core/gif_builder.py after checking Pillow, numpy and imageio. Do not run Python modules in browsers or Edge Functions. Transparency, adaptive palettes and tighter compression need separate tested implementations, not merely changed copy.


Regression finding: upstream optimize_for_emoji=True drops frames without preserving total duration. To preserve timing use optimize_for_emoji=False and remove_duplicates=False, applying only palette optimization. GIF delays have 10ms resolution: 12fps quantizes to 80ms/frame; display actual duration.
