"use client";

import { ChatState, useChatContext } from "@/hooks/useChatContext";
import { ChatMessage } from "@/types";
import { MessageCircle } from "lucide-react";
import { useState } from "react";
import ReactJson from "react-json-view";

interface ChatWindowProps {
  chatHistory: ChatMessage[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ chatHistory }) => {
  return (
    <div className="mb-4 h-[664px] w-4/5 max-w-7xl overflow-y-auto rounded-lg border border-gray-300 bg-white p-4">
      {chatHistory.map((message) => (
        <div key={message.id} className={`mb-4 rounded-lg p-3 ${message.isUserMessage ? "self-end bg-[#fff0ef]" : "self-start bg-[#effeff]"}`}>
          <ChatMessageContent message={message.message} />
          {/* {!message.isUserMessage && (
            <div className="mt-8 grid grid-cols-2 gap-4">
              <MetricItem label="Model" value={message.model!} />
              <MetricItem label="Response Time" value={`${message.elapsedTime!.toFixed(2)} ms`} />
              <MetricItem label="Input Tokens" value={message.inputTokenCount!} />
              <MetricItem label="Input Cost" value={`${(message.inputTokenCount! * 0.000005).toFixed(4)} $`} />
              <MetricItem label="Output Tokens" value={message.outputTokenCount!} />
              <MetricItem label="Output Cost" value={`${(message.outputTokenCount! * 0.00001).toFixed(4)} $`} />
            </div>
          )} */}
        </div>
      ))}
    </div>
  );
};

const MetricItem: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div>
    <p className="text-sm font-medium text-muted-foreground">{label}</p>
    <p className="text-lg font-semibold">{value}</p>
  </div>
);

interface ChatMessageContentProps {
  message: string;
}

const ChatMessageContent: React.FC<ChatMessageContentProps> = ({ message }) => {
  let content;
  try {
    const parsedMessage = JSON.parse(message);
    content = (
      <ReactJson src={parsedMessage} name={null} theme="apathy:inverted" iconStyle="triangle" indentWidth={2} collapsed={false} displayDataTypes={false} enableClipboard={false} />
    );
  } catch (e) {
    content = <div>{message}</div>;
  }

  return content;
};

interface MessageInputProps {
  currentMessage: string;
  setCurrentMessage: (message: string) => void;
  handleSendMessage: () => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ currentMessage, setCurrentMessage, handleSendMessage }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentMessage(e.target.value);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <div className="flex w-4/5 max-w-3xl">
      <input
        type="text"
        value={currentMessage}
        onChange={handleChange}
        onKeyPress={handleKeyPress}
        placeholder="Type your message here..."
        className="flex-1 rounded-l-lg border border-gray-300 p-2"
      />
      <button onClick={handleSendMessage} className="rounded-r-lg border border-l-0 border-gray-300 bg-blue-500 p-2 text-white hover:bg-blue-600">
        Send
      </button>
    </div>
  );
};

const ChatComponent = () => {
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const { state, data, actions } = useChatContext();

  const handleSendMessage = () => {
    console.log(`state.chatState: ${state.chatState}`);
    if (state.chatState !== ChatState.Typing) return;
    actions.handleSendMessage(currentMessage);
    setCurrentMessage("");
  };

  return (
    <div className="flex min-h-screen flex-col items-center bg-background">
      <header className="flex items-start border-b bg-card px-4 py-3 sm:px-6">
        <div className="flex items-start gap-4">
          <MessageCircle className="h-6 w-6 text-card-foreground" />
          <h1 className="text-lg font-semibold text-card-foreground">Chatbot</h1>
        </div>
      </header>
      <ChatWindow chatHistory={data.chatHistory} />
      <MessageInput currentMessage={currentMessage} setCurrentMessage={setCurrentMessage} handleSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatComponent;
