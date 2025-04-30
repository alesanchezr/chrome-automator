This project can be used to automate first contacts followups to 4Geeks.com Self Paced Leads

1. Make sure to add the deepseek API key in a new .env file

```txt
DEEPSEEK_API_KEY=asdasdadsdas
```

2. Start chrome with remote debugging flag:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile"
```

or Linux/Ubuntu:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile"
```

or windows:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-dev-profile"
```

3. Run the follow up process but make sure to replace the `<list-slug>`:

```bash
python src/followup-next.py --list=<list-slug>
```