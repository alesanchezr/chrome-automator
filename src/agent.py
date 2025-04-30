from langchain_openai import ChatOpenAI
from browser_use import Agent as BrowserAgent, BrowserConfig, Browser
import asyncio
from pydantic import SecretStr
import os



class Agent:
    _instance = None
    _initialized = False

    def __new__(cls, name="Flor", on_complete=None):
        if cls._instance is None:
            cls._instance = super(Agent, cls).__new__(cls)
            cls._instance.name = name
            cls._instance.on_complete = on_complete
        return cls._instance

    def __init__(self, name="Flor", on_complete=None):
        if not Agent._initialized:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            self.llm = ChatOpenAI(base_url='https://api.deepseek.com/v1', model='deepseek-chat', api_key=SecretStr(api_key))
            self.b_config = BrowserConfig(
                browser_binary_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                initial_urls=[
                    "https://app.brevo.com/crm/deals/kanban?pipeline=66f5835877486769ad130fd6&sortBy=created_at&sort=desc",
                    "https://web.whatsapp.com/"
                ]
            )
            self.browser = Browser(config=self.b_config)
            self.tasks = []
            self.on_complete = on_complete
            Agent._initialized = True

    def addTasks(self, tasks):
        """Add tasks to the agent's task list"""
        if isinstance(tasks, tuple):
            self.tasks.extend(tasks)
        else:
            self.tasks.append(tasks)
        return self

    async def _run(self):
        """Internal async run method"""
        agent = BrowserAgent(
            task=self.tasks,
            save_conversation_path="logs/conversation",
            llm=self.llm,
            browser=self.browser,
        )
        result = await agent.run()
        print("result", result)
        
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