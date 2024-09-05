"use client";

import { ChatState, useChatContext } from "@/hooks/useChatContext";
import { MessageCircle } from "lucide-react";
import React, { memo, useCallback, useState } from "react";
import ChatWindow from "../blocks/ChatWindow";
import MessageInput from "../blocks/MessageInput";

const ChatComponent: React.FC = () => {
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const { state, data, actions } = useChatContext();

  const handleSendMessage = useCallback(() => {
    if (state.chatState !== ChatState.Typing) return;
    actions.sendMessage(currentMessage);
    setCurrentMessage("");
  }, [state.chatState, actions, currentMessage]);

  return (
    <div className="flex h-full flex-col items-center bg-background">
      <ChatHeader />
      <ChatWindow chatHistory={data.chatHistory} />
      <MessageInput
        currentMessage={currentMessage}
        setCurrentMessage={setCurrentMessage}
        handleSendMessage={handleSendMessage}
        isDisabled={state.chatState !== ChatState.Typing}
      />
    </div>
  );
};

const ChatHeader: React.FC = memo(function ChatHeader() {
  return (
    <header className="flex items-start border-b bg-card px-4 py-3 sm:px-6">
      <div className="flex items-start gap-4">
        <MessageCircle className="h-6 w-6 text-card-foreground" />
        <h1 className="text-lg font-semibold text-card-foreground">Chatbot</h1>
      </div>
    </header>
  );
});

export default memo(ChatComponent);
