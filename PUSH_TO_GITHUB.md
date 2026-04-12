# Push to GitHub Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in:
   - Repository name: `hubitat-alarm-hacs`
   - Description: `Home Assistant HACS integration for Hubitat Alarm (DSC/Honeywell)`
   - Visibility: **Public** (required for HACS)
   - **DO NOT check any boxes** (no README, .gitignore, or license)
3. Click "Create repository"

## Step 2: Push Your Code

After creating the repo, run these commands:

```bash
cd "/Users/michettik/Projects/HomeAssistant Alarm"

# Add your GitHub repo (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/hubitat-alarm-hacs.git

# Push to GitHub
git push -u origin main
```

## Step 3: Verify on GitHub

Visit your repo and confirm all files are there:
- README.md with attribution
- custom_components/hubitat_alarm/ folder
- hacs.json
- LICENSE

## Next: Install in Home Assistant

See INSTALL.md for installation instructions.
