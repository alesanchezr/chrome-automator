# Chrome Automator for 4Geeks Followups

This project can be used to automate first contacts followups to 4Geeks.com Self Paced Leads


## Setup Instructions / Instrucciones de configuración

### 1. Create and activate a virtual environment / Crear y activar un entorno virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies / Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file / Crear un archivo `.env`

Add the following configuration (Agrega la siguiente configuración):
```properties
DEEPSEEK_API_KEY=your_api_key_here
ENVIRONMENT=development  # or 'production'
CHROME_EXECUTABLE="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Windows default
DEBUG=true
REMOTE_DEBUGGING_PORT=9222
```

**Linux:**
CHROME_EXECUTABLE="/usr/bin/google-chrome"

**macOS:**
CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

### 4. Start Chrome with remote debugging / Iniciar Chrome con depuración remota

**Windows:**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-dev-profile"
```

**Linux/macOS:**
```bash
# Close any existing Chrome instances / Cierra cualquier instancia de Chrome existente
pkill -f 'chrome' || true
# Start Chrome / Inicia Chrome
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-dev-profile
# macOS: use the CHROME_EXECUTABLE path above if needed
```

### 5. Run the agent / Ejecutar el agente

Replace `<list-slug>` with your list name (Reemplaza `<list-slug>` por el nombre de tu lista):
```bash
python src/followup-next.py --list=<list-slug>
```

**Example / Ejemplo:**
```bash
python src/followup-next.py --list=4ga-lost
```

---

## Quick Summary (EN/ES)

- Works on Windows, Linux, and macOS / Funciona en Windows, Linux y macOS
- Requires Python 3.8+ / Requiere Python 3.8+
- Needs Chrome installed / Necesita Chrome instalado
- You must set up your `.env` file / Debes configurar tu archivo `.env`
- Start Chrome with remote debugging / Inicia Chrome con depuración remota
- Run the agent script / Ejecuta el script del agente

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
