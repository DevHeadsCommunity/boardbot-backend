from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents import AgentType
from .langchain_llm_adapter import LangchainChatModelAdapter
from .openai_service import OpenAIService

class SQLQueryAgent:
    def __init__(self, db_uri: str, openai_service: OpenAIService):
        self.db = SQLDatabase.from_uri(db_uri)
        self.openai_service = openai_service
        self.agent_executor = None

    async def initialize(self):
        await self.openai_service.initialize()

        # Use the adapter instead of ChatOpenAI
        llm = LangchainChatModelAdapter(openai_service=self.openai_service)

        toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
        self.agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True, handle_parsing_errors=True)

    async def query(self, natural_language: str) -> str:
        if self.agent_executor is None:
            await self.initialize()

        try:
            return await self.agent_executor.arun(natural_language)
        except Exception as e:
            result = str(e)

        if "Final Answer:" in result:
            result = result.split("Final Answer:")[-1].strip()
        return result
