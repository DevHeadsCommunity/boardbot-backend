import React, { memo } from "react";

interface UserMessageProps {
  message: string;
}

const UserMessage: React.FC<UserMessageProps> = memo(function UserMessage({ message }) {
  return <div className="break-words text-right">{message}</div>;
});

export default UserMessage;
