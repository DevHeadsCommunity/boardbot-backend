from tavily import TavilyClient


class TavilyService:
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    async def search(self, query: str) -> dict:
        try:
            return self.client.search(query)
        except Exception as e:
            print(f"Error in Tavily search: {str(e)}")
            raise
