from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
import asyncio
from pydantic import SecretStr
import os
import platform
import requests

## Dictionary mapping operating systems to Chrome binary paths
# EN: Maps each OS to the default Chrome executable path
# ES: Asocia cada sistema operativo con la ruta del ejecutable de Chrome
CHROME_PATHS = {
    'darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    'windows': "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",     # Windows
    'linux': "/usr/bin/google-chrome"                                          # Debian-based Linux
}

## System mapping to normalize platform.system() output
# EN: Normalizes platform.system() output to match our CHROME_PATHS keys
# ES: Normaliza la salida de platform.system() para coincidir con las claves de CHROME_PATHS
SYSTEM_MAP = {
    'darwin': 'darwin',      # macOS
    'mac': 'darwin',         # Alternative macOS name
    'macos': 'darwin',       # Alternative macOS name
    'windows': 'windows',    # Windows
    'win32': 'windows',      # Alternative Windows name
    'win64': 'windows',      # Alternative Windows name
    'linux': 'linux',        # Linux
    'linux2': 'linux',       # Alternative Linux name
}

## Main agent class for browser automation
# EN: This class controls the browser and LLM for WhatsApp automation
# ES: Esta clase controla el navegador y el LLM para la automatización de WhatsApp
class BrowserAgent:
    def __init__(self, name="Flor", on_complete=None):
        # EN: Initialize the agent with name and completion callback
        # ES: Inicializa el agente con nombre y callback de finalización
        self.name = name
        self.on_complete = on_complete
        
        # Try to initialize LLM with available API keys
        # EN: Try to initialize the LLM (AI model) with available API keys
        # ES: Intenta inicializar el LLM (modelo de IA) con las claves API disponibles
        self.llm = self._initialize_llm()
        if not self.llm:
            raise ValueError("No valid API key found. Please set either OPENAI_API_KEY or DEEPSEEK_API_KEY in your .env file.")
        
        # Detect and normalize system
        # EN: Detect and normalize the operating system
        # ES: Detecta y normaliza el sistema operativo
        raw_system = platform.system().lower()
        self.system = SYSTEM_MAP.get(raw_system)
        if not self.system:
            raise OSError(f"Unsupported operating system: {raw_system}. Please add it to SYSTEM_MAP.")
        
        # Get the appropriate Chrome path based on the system
        # EN: Get the Chrome executable path for the current OS
        # ES: Obtiene la ruta del ejecutable de Chrome para el sistema actual
        chrome_path = CHROME_PATHS.get(self.system)
        if not chrome_path:
            raise OSError(f"Chrome path not configured for system: {self.system}. Please add it to CHROME_PATHS.")
        
        # EN: Configure the browser for WhatsApp automation
        # ES: Configura el navegador para la automatización de WhatsApp
        self.b_config = BrowserConfig(
            browser_binary_path=chrome_path,
            initial_urls=[
                "https://web.whatsapp.com/"
            ],
            system_prompt="""You are a WhatsApp automation agent. Follow these instructions exactly:
            1. When opening WhatsApp Web, wait for the QR code or chat interface to load
            2. Handle any permission prompts by clicking Block/Deny or pressing Escape
            3. For sending messages:
               - Find the input box with placeholder 'Type a message'
               - For each message:
                 * Click inside the input box
                 * Type the entire message as a single block
               - Only when the full message is ready, click the send button (paper plane icon) ONCE
               - Wait to see double checkmarks (✓✓) before proceeding
            4. Never send a message in parts - each task's content must be sent as one complete message
            5. Avoid sending the message prematurely"""
        )
        self.browser = Browser(config=self.b_config)
        self.tasks = []

    def _initialize_llm(self):
        # EN: Initialize the LLM using DeepSeek or OpenAI API keys
        # ES: Inicializa el LLM usando las claves API de DeepSeek o OpenAI
        """Initialize LLM with available API keys, trying DeepSeek first, then OpenAI"""
        # Try DeepSeek first
        # EN: Try DeepSeek API first
        # ES: Prueba primero la API de DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                # Test the DeepSeek API
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {deepseek_key}"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1
                    },
                    timeout=10
                )
                
                # If we get any response other than 402 (insufficient balance), use DeepSeek
                if response.status_code != 402:
                    print("✅ Using DeepSeek API")
                    os.environ["OPENAI_API_KEY"] = deepseek_key
                    return ChatOpenAI(
                        base_url="https://api.deepseek.com/v1",
                        model="deepseek-chat",
                        api_key=SecretStr(deepseek_key),
                    )
                else:
                    print("⚠️ DeepSeek API has insufficient balance, trying OpenAI...")
            except Exception as e:
                print(f"⚠️ DeepSeek API test failed: {e}, trying OpenAI...")
        
        # Try OpenAI
        # EN: If DeepSeek fails, try OpenAI API
        # ES: Si falla DeepSeek, prueba la API de OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.strip():
            try:
                print("✅ Using OpenAI API")
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=SecretStr(openai_key),
                )
            except Exception as e:
                print(f"❌ OpenAI API initialization failed: {e}")
        
        print("❌ No valid API key found. Please check your .env file.")
        return None

    def addTasks(self, tasks):
        # EN: Add one or more tasks to the agent
        # ES: Agrega una o más tareas al agente
        """Add tasks to the agent's task list"""
        if isinstance(tasks, tuple):
            self.tasks.extend(tasks)
        else:
            self.tasks.append(tasks)
        return self

    async def _run(self):
        # EN: Run the agent asynchronously in the browser
        # ES: Ejecuta el agente de forma asíncrona en el navegador
        """Internal async run method"""
        agent = Agent(
            task=self.tasks,
            use_vision=False,
            save_conversation_path="logs/conversation",
            llm=self.llm,
            browser=self.browser,
        )
        result = await agent.run()
        
        # Call the callback if it exists
        if self.on_complete:
            self.on_complete(result)
            
        return result

    def run(self):
        # EN: Run the agent's tasks synchronously
        # ES: Ejecuta las tareas del agente de forma síncrona
        """Run the agent's tasks"""
        return asyncio.run(self._run())

    async def close(self):
        # EN: Close the browser session
        # ES: Cierra la sesión del navegador
        """Close the browser"""
        await self.browser.close() 
