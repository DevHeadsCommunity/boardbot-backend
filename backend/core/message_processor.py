import time
from generators.agent_v1 import AgentV1
from generators.agent_v2 import AgentV2
from generators.semantic_router_v1 import SemanticRouterV1
from models.message import Message, ResponseMessage


class MessageProcessor:
    def __init__(self, semantic_router_v1: SemanticRouterV1, agent_v1: AgentV1, agent_v2: AgentV2):
        self.agent_v1 = agent_v1
        self.agent_v2 = agent_v2
        self.semantic_router_v1 = semantic_router_v1

    async def process_message(self, message: Message, chat_history: list[Message]) -> ResponseMessage:
        start_time = time.time()

        if message.architecture_choice == "semantic-router-v1":
            response_content, stats = await self.semantic_router_v1.run(message, chat_history)
        elif message.architecture_choice == "agentic-v1":
            response_content, stats = await self.agent_v1.run(message.content, chat_history)
        elif message.architecture_choice == "agentic-v2":
            response_content, stats = await self.agent_v2.run(message.content, chat_history)
        else:
            raise ValueError(f"Unknown architecture choice: {message.architecture_choice}")

        elapsed_time = str(time.time() - start_time)

        return ResponseMessage(
            session_id=message.session_id,
            id=f"{message.id}_response",
            content=response_content,
            timestamp=elapsed_time,
            is_complete=True,
            input_token_count=stats["input_token_count"],
            output_token_count=stats["output_token_count"],
            elapsed_time=elapsed_time,
        )
