from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
import asyncio
from pydantic import SecretStr
import os
import platform

# Dictionary mapping operating systems to Chrome binary paths
CHROME_PATHS = {
    'darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    'win32': "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",     # Windows
    'windows': "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",     # Windows
    'linux': "/usr/bin/google-chrome"                                          # Debian-based Linux
}

class BrowserAgent:
    _instance = None
    _initialized = False

    def __new__(cls, name="Flor", on_complete=None):
        if cls._instance is None:
            cls._instance = super(BrowserAgent, cls).__new__(cls)
            cls._instance.name = name
            cls._instance.on_complete = on_complete
        return cls._instance

    def __init__(self, name="Flor", on_complete=None):
        if not BrowserAgent._initialized:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY environment variable is not set. Please add it to your .env file.")
            os.environ["OPENAI_API_KEY"] = api_key
            
            self.llm = ChatOpenAI(
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
                api_key=SecretStr(api_key),
            )
            
            # Get the appropriate Chrome path based on the operating system
            system = platform.system().lower()
            chrome_path = CHROME_PATHS.get(system)
            if not chrome_path:
                raise OSError(f"Unsupported operating system: {system}. Please add the Chrome path for this system to CHROME_PATHS.")
            
            self.b_config = BrowserConfig(
                browser_binary_path=chrome_path,
                initial_urls=[
                    "https://app.brevo.com/crm/deals/kanban?pipeline=66f5835877486769ad130fd6&sortBy=created_at&sort=desc",
                    "https://web.whatsapp.com/"
                ]
            )
            self.browser = Browser(config=self.b_config)
            self.tasks = []
            self.on_complete = on_complete
            BrowserAgent._initialized = True

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
        print("running.....", self.llm)
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