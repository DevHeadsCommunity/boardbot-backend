import React, { memo } from "react";

interface MessageInputProps {
  currentMessage: string;
  setCurrentMessage: (message: string) => void;
  handleSendMessage: () => void;
  isDisabled: boolean;
}

const MessageInput: React.FC<MessageInputProps> = memo(function MessageInput({ currentMessage, setCurrentMessage, handleSendMessage, isDisabled }) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentMessage(e.target.value);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isDisabled) {
      handleSendMessage();
    }
  };

  return (
    <div className="flex w-full max-w-7xl">
      <input
        type="text"
        value={currentMessage}
        onChange={handleChange}
        onKeyPress={handleKeyPress}
        placeholder="Type your message here..."
        className="flex-1 rounded-l-lg border border-gray-300 p-2"
        disabled={isDisabled}
      />
      <button
        onClick={handleSendMessage}
        className="rounded-r-lg border border-l-0 border-gray-300 bg-blue-500 p-2 text-white hover:bg-blue-600 disabled:bg-gray-400"
        disabled={isDisabled}
      >
        Send
      </button>
    </div>
  );
});

export default MessageInput;
