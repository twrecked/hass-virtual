# 🚀 Virtual v0.10.0-alpha.3 — Virtual Camera Platform & Live HLS Streaming

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.3

### 1. New Virtual Platform: `camera` (`Camera`)
Adds support for virtual security and CCTV cameras to test dashboard Picture Entity Cards, camera proxy streaming, automations, and live video feeds:

- **Picture Entity Card Support (`async_camera_image`)**:
  - Configure `image_url` with remote HTTP/HTTPS URLs or local file paths (e.g. `/local/camera.jpg` or paths within the Home Assistant config directory).
  - Automatically negotiates content type (`image/jpeg` vs `image/png`) based on headers or file extensions.
  - Path traversal protection to ensure local file access resides strictly within the Home Assistant configuration directory.
  - Built-in embedded offline JPEG fallback placeholder so picture cards never display broken image icons.
- **Live Stream Support (`stream_source`)**:
  - Defaults out-of-the-box to the public Mux Big Buck Bunny HLS test stream (`https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8`), allowing instant live video testing without needing physical cameras or complex RTSP servers.
  - Supports custom HLS (`.m3u8`), RTSP, or HTTP/MP4 streams.
  - Automatically enables `CameraEntityFeature.STREAM`; setting `stream_url` to `none` or `""` cleanly disables streaming for snapshot-only mode.
- **Power Controls (`CameraEntityFeature.ON_OFF`)**:
  - Full support for `camera.turn_on` and `camera.turn_off`.
- **Dynamic Services**:
  - `virtual.set_image_url`: Dynamically change snapshot URL or local file path in automations.
  - `virtual.set_stream_url`: Dynamically change live stream feed URL.

```yaml
Front Porch:
  - platform: camera
    name: Front Porch Camera
    image_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=640"
    stream_url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
```

---

### 2. Virtual Device Editor Updates
- Added `camera` platform support (expanding the editor to all 17 supported platforms).
- Added the **Security Camera** pre-configured device template for one-click setup.
- Added visual form controls for `image_url` and `stream_url`.
