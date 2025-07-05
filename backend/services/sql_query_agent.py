from services.langchain_llm_adapter import LangchainChatModelAdapter

class SQLQueryAgent:
    def __init__(self, db_uri: str, openai_service: OpenAIService):
        self.db = SQLDatabase.from_uri(db_uri)
        self.openai_service = openai_service
        self.agent_executor = None

    async def initialize(self):
        await self.openai_service.initialize()

        # Use the adapter instead of ChatOpenAI
        llm = LangchainChatModelAdapter(self.openai_service)

        toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
        self.agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)

    async def query(self, natural_language: str) -> str:
        if self.agent_executor is None:
            await self.initialize()
        return await self.agent_executor.arun(natural_language)
