# Chrome Automator for 4Geeks Followups

This project can be used to automate first contacts followups to 4Geeks.com Self Paced Leads

## Setup Instructions

1. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following configuration:

```properties
DEEPSEEK_API_KEY=your_api_key_here
ENVIRONMENT=development  # or 'production'
CHROME_EXECUTABLE="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Windows default
DEBUG=true
REMOTE_DEBUGGING_PORT=9222
```

Note: For other operating systems, use these paths for CHROME_EXECUTABLE:
- Linux: `/usr/bin/google-chrome`
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

### Environment Modes

The application supports two modes:

- **Development Mode** (`ENVIRONMENT=development`):
  - Only processes contacts with @4geeksacademy.com email addresses
  - Other contacts are skipped and left in PENDING status
  - Useful for testing message templates and flows

- **Production Mode** (`ENVIRONMENT=production`):
  - Processes all contacts regardless of email domain
  - Use this mode for real follow-up campaigns

## Running the Application

1. Start Chrome with remote debugging:

```bash
# Windows (recommended)
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-dev-profile"

# Alternative for Linux/macOS
# First close any existing Chrome instances:
pkill -f 'chrome' || true
# Then start Chrome with debugging:
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-dev-profile
```

2. Run the followup process (replace `<list-slug>` with your list name):

```bash
python src/followup-next.py --list=<list-slug>
```

### Example List Usage

```bash
# For 4Geeks Lost Customers follow-up
python src/followup-next.py --list=4ga-lost
```

## Development

If you add new dependencies to the project, make sure to update requirements.txt:

```bash
pip freeze > requirements.txt
```

## Production Setup

When running in production mode:

1. Set `ENVIRONMENT=production` in your `.env` file
2. Ensure Chrome is not running before starting the automation
3. Consider using a dedicated Chrome profile to avoid conflicts
4. Test your message templates with development mode first

### Status Flow

The automation follows this status flow for each contact:

1. `PENDING` - Initial state for new contacts
2. `STARTED` - Contact is being processed
3. `COMPLETE` - Messages sent successfully
4. `ERROR` - Error during processing (with error details in status text)

## Troubleshooting

### Chrome Issues

1. If Chrome fails to start:

Windows:
   ```bash
   # Kill any existing Chrome processes (run in PowerShell as Administrator)
   taskkill /F /IM chrome.exe
   # Remove test profile (optional)
   Remove-Item -Path "$env:TEMP\chrome-dev-profile" -Recurse -Force
   ```

Linux/macOS:
   ```bash
   # Kill any existing Chrome processes
   pkill -f 'chrome'
   # Remove test profile (optional)
   rm -rf /tmp/chrome-dev-profile
   ```

2. If WhatsApp Web doesn't load:
   - Ensure you're logged in to WhatsApp Web in your Chrome profile
   - Check your internet connection
   - Verify the phone number format in the contact data

### Message Processing

1. Development Mode:
   - Only @4geeksacademy.com contacts are processed
   - Other contacts remain in PENDING status
   - Use this mode to test your message templates

2. Production Mode:
   - All contacts are processed regardless of email domain
   - Messages are personalized using contact data
   - Status updates are logged for tracking