import logging
from typing import List, Dict, Any, Set
from tavily import TavilyClient
from urllib.parse import urlparse
import asyncio
from functools import partial
from services.utils.enhanced_error_logger import create_error_logger
logger = logging.getLogger(__name__)
logger.error = create_error_logger(logger)

class TavilyService:
    def __init__(self, api_key: str, max_retries: int = 3):
        # self.api_key = api_key # TODO: identify the bug
        self.api_key = "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"
        self.client = None
        self.max_retries = max_retries

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        if self.client is None:
            self.client = TavilyClient(api_key=self.api_key)
        logger.debug("Tavily client connected.")

    async def close(self):
        self.client = None
        logger.debug("Tavily client closed.")

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def remove_redundant_domains(urls: List[str]) -> Set[str]:
        return set(TavilyService.normalize_url(url) for url in urls)

    async def search(self, query: str, exclude_domains: List[str] = None) -> List[Dict[str, Any]]:
        normalized_exclude = self.remove_redundant_domains(exclude_domains or [])
        logger.info(f"Normalized exclude domains: {normalized_exclude}")

        results = await self._perform_search(query, normalized_exclude)

        if not results:
            logger.warning("No results found with exclude domains. Retrying without exclusions.")
            results = await self._perform_search(query, set())

        filtered_results = self._filter_results(results, exclude_domains or [])
        return self._format_results(filtered_results, query)

    async def _perform_search(self, query: str, exclude_domains: Set[str]) -> List[Dict[str, Any]]:
        for attempt in range(self.max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self.client.search,
                        query,
                        search_depth="advanced",
                        max_results=10,
                        include_raw_content=True,
                        exclude_domains=list(exclude_domains),
                    ),
                )
                return response.get("results", [])
            except Exception as e:
                logger.error(f"Error in Tavily search (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _filter_results(self, results: List[Dict[str, Any]], exclude_domains: List[str]) -> List[Dict[str, Any]]:
        return [result for result in results if result.get("url", "") not in exclude_domains]

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        formatted_results = []
        for result in results:
            formatted_result = {
                "search_query": query,
                "search_result": self._combine_content(result),
                "data_source": result.get("url", ""),
            }
            formatted_results.append(formatted_result)
        logger.info(f"Formatted {len(formatted_results)} results for query: {query}")
        return formatted_results

    def _combine_content(self, result: Dict[str, Any]) -> str:
        title = result.get("title", "")
        content = result.get("content", "")
        raw_content = result.get("raw_content", "")

        combined = f"Title: {title}\n\nSummary: {content}"
        if raw_content:
            combined += f"\n\nAdditional Details: {raw_content}"

        return combined
