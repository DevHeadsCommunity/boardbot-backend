import { ChatHistoryItem, ResponseMessage } from "@/types";
import React, { memo } from "react";
import BotResponse from "./BotResponse";
import UserMessage from "./UserMessage";

interface ChatWindowProps {
  chatHistory: ChatHistoryItem[];
}

const ChatWindow: React.FC<ChatWindowProps> = memo(function ChatWindow({ chatHistory }) {
  return (
    <div className="mx-auto mb-4 h-[664px] w-full max-w-7xl overflow-y-auto rounded-lg border border-gray-300 bg-white">
      {chatHistory.map((message) => (
        <div key={message.messageId} className={`mb-4 ${message.isUserMessage ? "flex justify-end" : "flex justify-start"}`}>
          <div className={`rounded-lg p-3 ${message.isUserMessage ? "max-w-[80%]  bg-blue-100 text-blue-900" : "w-full bg-gray-100 text-gray-900"}`}>
            {message.isUserMessage ? <UserMessage message={message.message} /> : <BotResponse message={message as ResponseMessage} />}
          </div>
        </div>
      ))}
    </div>
  );
});
export default ChatWindow;
