#!/usr/bin/env python3
"""
PC Doctor updater - checks for newer versions and installs them only with your approval.

How it works:
  1. Downloads a small manifest file from UPDATE_MANIFEST_URL. It looks like:
       {"version": "2.1.0", "url": "https://.../pc_doctor_complete_v3.py",
        "sha256": "the-file's-sha256-fingerprint"}
  2. If the manifest version is newer than this script's version, it tells you.
  3. If you say yes, it downloads the new file, checks its SHA-256 fingerprint
     against the manifest, and saves it as a NEW file. Your current script is
     never overwritten, so you can always go back.

Nothing updates silently. The script never runs downloaded code on its own.

Setup for you: set UPDATE_MANIFEST_URL below to the link where you host the
manifest. Leave it empty to turn update checks off.
"""

import hashlib
import json
import os
import urllib.request

SCRIPT_VERSION = "2.0.0"
UPDATE_MANIFEST_URL = ""  # Example: "https://yourhost.example/pc_doctor/latest.json"
DOWNLOAD_TIMEOUT = 30


def parse_version(text):
    """Turn '2.1.0' into (2, 1, 0) so versions compare correctly."""
    return tuple(int(part) for part in text.strip().split("."))


def fetch_manifest():
    """Return the manifest dict, or None if it can't be read."""
    if not UPDATE_MANIFEST_URL:
        return None
    try:
        with urllib.request.urlopen(UPDATE_MANIFEST_URL, timeout=DOWNLOAD_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not all(k in data for k in ("version", "url", "sha256")):
            return None
        return data
    except (OSError, ValueError):
        return None


def check_for_update():
    """Return the newer manifest if one exists, otherwise None."""
    manifest = fetch_manifest()
    if not manifest:
        return None
    try:
        if parse_version(manifest["version"]) > parse_version(SCRIPT_VERSION):
            return manifest
    except ValueError:
        return None
    return None


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_update(manifest, ask_yes_no):
    """Download and verify the new version, then save it beside the current one."""
    if not ask_yes_no(f"PC Doctor {manifest['version']} is available. Download it?"):
        print("Update skipped. You can check again later.")
        return None

    new_path = f"pc_doctor_{manifest['version']}.py"
    try:
        with urllib.request.urlopen(manifest["url"], timeout=DOWNLOAD_TIMEOUT) as response:
            content = response.read()
    except OSError as e:
        print(f"Download failed: {e}")
        return None

    # Save to a temporary file first and check its fingerprint before keeping it.
    temp_path = new_path + ".download"
    with open(temp_path, "wb") as f:
        f.write(content)

    if sha256_of(temp_path) != manifest["sha256"].lower():
        os.remove(temp_path)
        print("The downloaded file did not match its fingerprint, so it was discarded. "
              "Do not use it. Let the PC Doctor maintainer know.")
        return None

    os.replace(temp_path, new_path)
    print(f"Saved verified update as {os.path.abspath(new_path)}.")
    print("Run that file from now on. Your current version is still here if you need it.")
    return new_path


def run_update_check(ask_yes_no):
    """Entry point the main script can call at startup."""
    if not UPDATE_MANIFEST_URL:
        return  # Updates are turned off until a manifest link is set.
    manifest = check_for_update()
    if manifest:
        install_update(manifest, ask_yes_no)
    else:
        print(f"PC Doctor {SCRIPT_VERSION} is up to date (or the update server could not be reached).")
