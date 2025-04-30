# Chrome Automator for 4Geeks Followups

This project can be used to automate first contacts followups to 4Geeks.com Self Paced Leads

## Setup Instructions

1. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
playwright install
```

4. Create a `.env` file and add your Deepseek API key:

```txt
DEEPSEEK_API_KEY=your_api_key_here
```

## Running the Application

1. Start Chrome with remote debugging flag:

```bash
# On macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile"

# On Linux/Ubuntu:
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile"

# On Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-dev-profile"
```

2. Run the followup process (replace `<list-slug>` with your list name):

```bash
python src/followup-next.py --list=<list-slug>
```

## Development

If you add new dependencies to the project, make sure to update requirements.txt:

```bash
pip freeze > requirements.txt
```