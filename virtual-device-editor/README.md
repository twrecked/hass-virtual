# Virtual Device Editor

A web-based visual builder for managing Home Assistant [Virtual](https://github.com/twrecked/hass-virtual) devices and entities.

Hosted version available at: **[https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com)**

---

## Features

- **Visual Tree Builder**: Add and organize devices and child entities with an intuitive card-based UI.
- **Support for all 17 Platforms**: `alarm_control_panel`, `binary_sensor`, `button`, `camera`, `climate`, `cover`, `device_tracker`, `fan`, `light`, `lock`, `media_player`, `number`, `select`, `sensor`, `switch`, `text`, and `valve`.
- **Dynamic Field Validation**: Form fields automatically adjust to the chosen platform (color/brightness controls for lights, timing sliders for covers/valves, speed counts for fans, and standard Home Assistant device classes and units).
- **Device Templates**: One-click creation of common multi-entity devices (e.g. motion sensor with battery, dimmable lights, window blinds, power meter outlets, weather stations).
- **Live YAML Preview**: Real-time YAML generation side-by-side with your visual cards.
- **Automatic Home Assistant Sync**: If opened from Home Assistant's **Configure** dialog, clicking **Save & Return** automatically updates your YAML file on disk and reloads the integration via an authenticated webhook.
- **Manual Export & Import**: Full support for copying YAML to your clipboard, downloading the file, or pasting existing YAML directly into the editor.

---

## Running Locally (Private / Offline Mode)

If you prefer to run the editor locally on your home network without sending data through the cloud:

### 1. Requirements
* Python 3.10+
* Virtual environment (recommended)

### 2. Install & Run
```bash
cd virtual-device-editor
pip install -r requirements.txt
python main.py
```

The editor will start at: **`http://localhost:8080`** (and on your local network IP).

### 3. Connect to Home Assistant
In Home Assistant:
1. Go to **Settings -> Devices & Services -> Virtual**.
2. Click **Configure** on any group.
3. In the dialog, set **Editor URL** to your local address (e.g. `http://127.0.0.1:8080` or `http://192.168.1.X:8080`).
4. Click **Submit** to save your preference, then click **Open Virtual Device Editor**.

---

## Manual / Copy-Paste Fallback

If you don't use webhooks or have external access disabled:

1. Open the editor in your browser: [https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com).
2. Click **Import YAML** and paste your existing `virtual.yaml` content (or start from scratch with templates).
3. Make your edits visually.
4. Click **Copy** (or **Download**) in the top right bar.
5. Paste the YAML into your `/config/virtual.yaml` file using Home Assistant's File Editor or VS Code add-on.
6. In Home Assistant, go to **Settings -> Devices & Services -> Virtual**, click the three dots, and select **Reload**.

---

## Deployment to Google App Engine

The editor is configured as an App Engine service:

```bash
gcloud app deploy app.yaml
```
*(Make sure an App Engine `default` service is deployed in your GCP project first).*
