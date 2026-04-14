# FREE Automated Flight Checking with GitHub Actions

This runs on GitHub's servers (US-based) so there's NO EU consent wall!
Completely FREE - no credit card required.

## Setup (5 minutes)

### 1. Create a GitHub Account
- Go to https://github.com
- Sign up (free)

### 2. Create a New Repository
- Click "+" → "New repository"
- Name it: `ams-flights-watcher`
- Make it private (optional)
- Click "Create repository"

### 3. Upload These Files
Upload to your new repo:
- `ams_flights_github.py`
- `.github/workflows/flights.yml`

Or use GitHub web interface:
- Click "Add file" → "Upload files"
- Drag and drop the files
- Click "Commit changes"

### 4. Run It
- Go to "Actions" tab
- Click "AMS Flights Check"
- Click "Run workflow"
- Wait 2-3 minutes
- Download the results!

### 5. Schedule It (Automated)
The workflow is already set to run daily at 9 AM UTC.

To change the schedule, edit `.github/workflows/flights.yml`:
```yaml
schedule:
  - cron: '0 9 * * *'  # Daily at 9 AM UTC
```

Cron format:
- `0 9 * * *` = Daily at 9 AM
- `0 */6 * * *` = Every 6 hours
- `0 9 * * 1` = Weekly on Monday at 9 AM

## How It Works

1. GitHub Actions runs on US servers (no GDPR consent)
2. Script scans 20 European destinations
3. Results saved as JSON artifact
4. You download the results

## Cost: $0

GitHub gives you:
- 2,000 minutes/month free
- This script uses ~2 minutes per run
- You can run it 1,000 times per month for FREE

## Getting Results

### Option 1: Download from GitHub
- Go to Actions tab
- Click the latest run
- Download "flight-results" artifact

### Option 2: Send to Yourself (Advanced)
You can modify the workflow to:
- Email results to you
- Post to Slack/Discord
- Save to Google Sheets

## Files in This Setup

| File | Purpose |
|------|---------|
| `ams_flights_github.py` | Main script (GitHub version) |
| `.github/workflows/flights.yml` | Automation schedule |

## Troubleshooting

**If it fails:**
1. Check the Actions log
2. Most likely: Google changed something
3. The script will show errors in the log

**If you need more destinations:**
Edit `ams_flights_github.py` and add more airports to the list.
