import logging
from typing import List, Dict, Any
from tavily import TavilyClient

logger = logging.getLogger(__name__)


class TavilyService:
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    async def search(self, query: str, exclude_domains: List[str] = None) -> List[Dict[str, Any]]:
        try:
            response = self.client.search(
                query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True,
                exclude_domains=exclude_domains or [],
            )
            return self._format_results(response.get("results", []), query)
        except Exception as e:
            logger.error(f"Error in Tavily search: {str(e)}")
            raise

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        formatted_results = []
        for result in results:
            formatted_result = {
                "search_query": query,
                "search_result": self._combine_content(result),
                "data_source": result.get("url", ""),
            }
            formatted_results.append(formatted_result)
        return formatted_results

    def _combine_content(self, result: Dict[str, Any]) -> str:
        title = result.get("title", "")
        content = result.get("content", "")
        raw_content = result.get("raw_content", "")

        combined = f"Title: {title}\n\nSummary: {content}"
        if raw_content:
            combined += f"\n\nAdditional Details: {raw_content}"

        return combined
