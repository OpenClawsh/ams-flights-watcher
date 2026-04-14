#!/usr/bin/env python3
"""
Discord reporter for flight results
Run this locally to check GitHub Actions and post to Discord
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DISCORD_CHANNEL = "1493425182961041558"
REPO = "OpenClawsh/ams-flights-watcher"

def get_latest_run(workflow_name):
    """Get latest run ID for a workflow"""
    try:
        result = subprocess.run(
            ["gh", "run", "list", "--repo", REPO, "--workflow", workflow_name, 
             "--json", "databaseId,status,conclusion", "--limit", "1"],
            capture_output=True, text=True, check=True
        )
        runs = json.loads(result.stdout)
        if runs and runs[0]["conclusion"] == "success":
            return runs[0]["databaseId"]
    except Exception as e:
        print(f"Error getting run: {e}")
    return None

def download_artifact(run_id, artifact_name, output_file):
    """Download artifact from run"""
    try:
        subprocess.run(
            ["gh", "run", "download", str(run_id), "--repo", REPO, 
             "-n", artifact_name, "-D", "/tmp/flight_check"],
            capture_output=True, check=True
        )
        with open(f"/tmp/flight_check/{output_file}") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error downloading: {e}")
    return None

def format_general_results(data):
    """Format general flight results for Discord"""
    if not data or not data.get("results"):
        return "🔍 No general flight deals found today."
    
    lines = [
        "✈️ AMS Flight Deals (General)",
        f"Updated: {data['generated_at'][:10]}",
        ""
    ]
    
    for r in data["results"][:10]:
        dep = r["departure_date"][5:]
        ret = r["return_date"][5:]
        airlines = ", ".join(r["airlines"][:2])
        lines.append(f"• {r['name']} ({r['code']}): {dep} → {ret}, {r['trip_days']} days, €{r['price']}, {airlines}")
    
    lines.append("")
    lines.append(f"Constraints: Nonstop, round-trip, €{data['constraints']['price_cap_eur']} max, 3+ days, back by Tue")
    
    return "\n".join(lines)

def format_london_results(data):
    """Format London VCT results for Discord"""
    if not data or not data.get("results"):
        return "🏆 No London VCT deals found in the June window."
    
    window = data.get("window", {})
    lines = [
        "🎮 VCT Masters London - Special Search",
        f"Window: {window.get('start', 'N/A')} to {window.get('end', 'N/A')}",
        ""
    ]
    
    for r in data["results"][:10]:
        dep = r["departure_date"][5:]
        ret = r["return_date"][5:]
        airlines = ", ".join(r["airlines"][:2])
        lines.append(f"• {r['code']}: {dep} → {ret}, {r['trip_days']} days, €{r['price']}, {airlines}")
    
    lines.append("")
    lines.append("Book soon, VCT Masters London is popular.")
    
    return "\n".join(lines)

def send_to_discord(message):
    """Send message to Discord via OpenClaw messaging"""
    # This will be handled by OpenClaw's messaging system
    # The channel ID is: 1493425182961041558
    print(f"DISCORD_MESSAGE_TO_{DISCORD_CHANNEL}:")
    print(message)
    print("\nNOTE: this script still only prints the Discord payload. It does not send it by itself.")
    return True

def main():
    print("Checking for latest flight results...")
    
    # Get general flights
    general_run = get_latest_run("general.yml")
    general_data = None
    if general_run:
        general_data = download_artifact(general_run, "general-flights", "general_flights.json")
    
    # Get London flights  
    london_run = get_latest_run("london.yml")
    london_data = None
    if london_run:
        london_data = download_artifact(london_run, "london-flights", "london_flights.json")
    
    # Format messages
    messages = []
    if general_data:
        messages.append(format_general_results(general_data))
    if london_data:
        messages.append(format_london_results(london_data))
    
    if not messages:
        print("No successful runs found to report.")
        return
    
    # Send combined message
    full_message = "\n\n".join(messages)
    send_to_discord(full_message)
    
    print("\nReport ready for Discord!")

if __name__ == "__main__":
    main()
