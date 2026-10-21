#!/usr/bin/env python3
"""Virtual Device Editor - Web application for managing Home Assistant virtual devices."""

from __future__ import annotations

import base64
import json
import logging
import os
import ssl
import urllib.error
import urllib.request
import zlib
from typing import Any

from flask import Flask, jsonify, render_template, request
import yaml

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)


def _decode_data(encoded: str) -> str:
    """Decode raw or compressed base64 data."""
    try:
        raw = base64.b64decode(encoded)
        try:
            return zlib.decompress(raw).decode("utf-8")
        except Exception:
            return raw.decode("utf-8")
    except Exception as err:
        _LOGGER.warning("Could not decode payload: %s", err)
        return ""


@app.route("/")
def index():
    """Render the editor interface."""
    callback_url = request.args.get("cb", "")
    token = request.args.get("token", "")
    group_name = request.args.get("name", "virtual.yaml")
    raw_data = request.args.get("data", "")

    initial_yaml = ""
    if raw_data:
        initial_yaml = _decode_data(raw_data)

    return render_template(
        "editor.html",
        callback_url=callback_url,
        token=token,
        group_name=group_name,
        initial_yaml=initial_yaml,
    )


@app.route("/api/parse-yaml", methods=["POST"])
def parse_yaml_endpoint():
    """Parse YAML content and return structured JSON."""
    data = request.get_json(silent=True) or {}
    content = data.get("yaml", "")
    try:
        parsed = yaml.safe_load(content) or {}
        if not isinstance(parsed, dict):
            return jsonify({"error": "YAML root must be a mapping/dictionary"}), 400
        return jsonify({"data": parsed})
    except Exception as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/dump-yaml", methods=["POST"])
def dump_yaml_endpoint():
    """Convert JSON structure to clean YAML."""
    data = request.get_json(silent=True) or {}
    try:
        dumped = yaml.dump(
            data.get("data", {}),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
        return jsonify({"yaml": dumped})
    except Exception as err:
        return jsonify({"error": str(err)}), 400


@app.route("/api/save", methods=["POST"])
def save_endpoint():
    """Forward updated YAML to Home Assistant webhook callback."""
    data = request.get_json(silent=True) or {}
    callback_url = data.get("callback_url", "")
    token = data.get("token", "")
    yaml_content = data.get("yaml", "")

    if not callback_url:
        return jsonify({"error": "No callback URL provided"}), 400

    headers = {
        "Content-Type": "application/x-yaml",
    }
    if token:
        headers["X-Auth-Token"] = token

    try:
        req = urllib.request.Request(
            callback_url,
            data=yaml_content.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            _LOGGER.info("Successfully delivered save to %s (status %s)", callback_url, resp.status)
            return jsonify({"ok": True, "response": resp_body})
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="replace")
        _LOGGER.error("HTTP error saving to %s: %s - %s", callback_url, err.code, err_body)
        return jsonify({"error": f"HTTP {err.code}: {err_body}"}), err.code
    except Exception as err:
        _LOGGER.error("Failed to forward save to %s: %s", callback_url, err)
        return jsonify({"error": str(err)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    _LOGGER.info("Starting Virtual Device Editor on http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=True)
