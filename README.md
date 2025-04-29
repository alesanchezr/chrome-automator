

1. Start chrome with remote debugging flag:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-dev-profile"
```

2. Run the follow up process:

```bash
python src/followup-next.py --list=4ga-lost
```