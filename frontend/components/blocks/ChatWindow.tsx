import { ChatHistoryItem, ResponseMessage } from "@/types";
import React, { memo } from "react";
import BotResponse from "./BotResponse";
import UserMessage from "./UserMessage";

interface ChatWindowProps {
  chatHistory: ChatHistoryItem[];
}

const ChatWindow: React.FC<ChatWindowProps> = memo(function ChatWindow({ chatHistory }) {
  return (
    <div className="mb-4 h-[664px] w-4/5 max-w-7xl overflow-y-auto rounded-lg border border-gray-300 bg-white p-4">
      {chatHistory.map((message) => (
        <div key={message.messageId} className={`mb-4 rounded-lg p-3 ${message.isUserMessage ? "self-end bg-[#fff0ef]" : "self-start bg-[#effeff]"}`}>
          {message.isUserMessage ? <UserMessage message={message.message} /> : <BotResponse message={message as ResponseMessage} />}
        </div>
      ))}
    </div>
  );
});

export default ChatWindow;
