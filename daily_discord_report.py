#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = "OpenClawsh/ams-flights-watcher"
CHANNEL_ID = "1493425182961041558"
GH = "/opt/homebrew/bin/gh"
OPENCLAW = "/opt/homebrew/bin/openclaw"
STATE_DIR = Path("/Users/hf/.openclaw/workspace/ams-flights-watcher/.state")
STATE_FILE = STATE_DIR / "daily_discord_report_state.json"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def latest_success(workflow_file):
    res = run([
        GH, "run", "list", "--repo", REPO, "--workflow", workflow_file,
        "--json", "databaseId,conclusion", "--limit", "5",
    ])
    runs = json.loads(res.stdout)
    for r in runs:
        if r.get("conclusion") == "success":
            return r
    return None


def download_json(run_id, artifact_name, filename):
    tmp = Path(tempfile.mkdtemp(prefix="flight-report-"))
    try:
        run([GH, "run", "download", str(run_id), "--repo", REPO, "-n", artifact_name, "-D", str(tmp)])
        matches = list(tmp.rglob(filename))
        if not matches:
            raise FileNotFoundError(filename)
        with open(matches[0]) as f:
            return json.load(f)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fmt_general(data):
    results = data.get("results", [])[:5]
    if not results:
        return ["General trips", "• No matching general trips today."]
    lines = ["General trips"]
    for r in results:
        airlines = ", ".join(r.get("airlines", [])[:2])
        lines.append(f"• {r['name']} ({r['code']}), {r['departure_date'][5:]} → {r['return_date'][5:]}, {r['trip_days']} days, €{r['price']}, {airlines}")
    return lines


def fmt_london(data):
    results = [r for r in data.get("results", []) if r.get("trip_days", 0) >= 3][:7]
    if not results:
        return ["London, June 10 to 18", "• No matching London trips today."]
    lines = ["London, June 10 to 18"]
    for r in results:
        airlines = ", ".join(r.get("airlines", [])[:2])
        lines.append(f"• {r['code']}, {r['departure_date'][5:]} → {r['return_date'][5:]}, {r['trip_days']} days, €{r['price']}, {airlines}")
    return lines


def build_message(general_data, london_data):
    lines = ["✈️ AMS flight watch", "", *fmt_general(general_data), "", "🎮 VCT / London", *fmt_london(london_data)]
    return "\n".join(lines)


def send(message, dry_run=False):
    cmd = [OPENCLAW, "message", "send", "--channel", "discord", "--target", f"channel:{CHANNEL_ID}", "--message", message]
    if dry_run:
        cmd.append("--dry-run")
    return run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    general_run = latest_success("general.yml")
    london_run = latest_success("london.yml")
    if not general_run or not london_run:
        raise SystemExit("Missing successful workflow runs")

    current = {"general_run": general_run["databaseId"], "london_run": london_run["databaseId"]}
    if not args.force and load_state() == current:
        print("No new successful runs since last sent report.")
        return

    general_data = download_json(general_run["databaseId"], "general-flights", "general_flights.json")
    london_data = download_json(london_run["databaseId"], "london-flights", "london_flights.json")
    msg = build_message(general_data, london_data)
    res = send(msg, dry_run=args.dry_run)
    if args.dry_run:
        print(res.stdout)
    else:
        save_state(current)
        print("Sent report to Discord.")


if __name__ == "__main__":
    main()
