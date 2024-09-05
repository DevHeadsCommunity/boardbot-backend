import React, { memo } from "react";
import ReactJson from "react-json-view";

interface ChatMessageContentProps {
  message: string;
}

const ChatMessageContent: React.FC<ChatMessageContentProps> = memo(function ChatMessageContent({ message }) {
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
});

export default ChatMessageContent;
