from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
import asyncio
from pydantic import SecretStr
import os
import platform

# Dictionary mapping operating systems to Chrome binary paths
CHROME_PATHS = {
    'darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    'windows': "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",     # Windows
    'linux': "/usr/bin/google-chrome"                                          # Debian-based Linux
}

# System mapping to normalize platform.system() output
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

class BrowserAgent:
    def __init__(self, name="Flor", on_complete=None):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set. Please add it to your .env file.")
        os.environ["OPENAI_API_KEY"] = api_key
        
        self.name = name
        self.on_complete = on_complete
        
        self.llm = ChatOpenAI(
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            api_key=SecretStr(api_key),
        )
        
        # Detect and normalize system
        raw_system = platform.system().lower()
        self.system = SYSTEM_MAP.get(raw_system)
        if not self.system:
            raise OSError(f"Unsupported operating system: {raw_system}. Please add it to SYSTEM_MAP.")
        
        # Get the appropriate Chrome path based on the system
        chrome_path = CHROME_PATHS.get(self.system)
        if not chrome_path:
            raise OSError(f"Chrome path not configured for system: {self.system}. Please add it to CHROME_PATHS.")
        
        self.b_config = BrowserConfig(
            browser_binary_path=chrome_path,
            initial_urls=[
                "https://app.brevo.com/crm/deals/kanban?pipeline=66f5835877486769ad130fd6&sortBy=created_at&sort=desc",
                "https://web.whatsapp.com/"
            ]
        )
        self.browser = Browser(config=self.b_config)
        self.tasks = []

    def addTasks(self, tasks):
        """Add tasks to the agent's task list"""
        if isinstance(tasks, tuple):
            self.tasks.extend(tasks)
        else:
            self.tasks.append(tasks)
        return self

    async def _run(self):
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
        """Run the agent's tasks"""
        return asyncio.run(self._run())

    async def close(self):
        """Close the browser"""
        await self.browser.close() 