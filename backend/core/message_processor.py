import time
from generators.llm_router import LLMRouter
from generators.dynamic_agent import DynamicAgent
from generators.hybrid_router import HybridRouter
from generators.semantic_router import SemanticRouter
from models.message import Message, ResponseMessage


class MessageProcessor:

    def __init__(
        self,
        llm_router: LLMRouter,
        semantic_router: SemanticRouter,
        hybrid_router: HybridRouter,
        dynamic_agent: DynamicAgent,
    ):
        self.llm_router = llm_router
        self.semantic_router = semantic_router
        self.hybrid_router = hybrid_router
        self.dynamic_agent = dynamic_agent

    async def process_message(self, message: Message) -> ResponseMessage:
        print(f"*** Processing message: {message.content}")
        start_time = time.time()

        if message.architecture_choice == "llm-router":
            response_content, stats = await self.llm_router.run(message)
        elif message.architecture_choice == "semantic-router":
            response_content, stats = await self.semantic_router.run(message)
        elif message.architecture_choice == "hybrid-router":
            response_content, stats = await self.hybrid_router.run(message)
        elif message.architecture_choice == "dynamic-agent":
            response_content, stats = await self.dynamic_agent.run(message)
        else:
            raise ValueError(f"Unknown architecture choice: {message.architecture_choice}")

        elapsed_time = str(time.time() - start_time)
        response_message = response_content.replace("```", "").replace("json", "").replace("\n", "").strip()

        return ResponseMessage(
            session_id=message.session_id,
            id=f"{message.id}_response",
            content=response_message,
            timestamp=elapsed_time,
            is_complete=True,
            input_token_count=stats["input_token_count"],
            output_token_count=stats["output_token_count"],
            elapsed_time=elapsed_time,
            model=message.model,
        )
