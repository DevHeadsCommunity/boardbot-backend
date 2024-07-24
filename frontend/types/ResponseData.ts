import { ChatMessage } from "./ChatMessage";

export interface ResponseData {
  type: string;
  sessionId: string;
  messageId: string;
  message: string;
  isComplete: boolean;
  chatHistory?: ChatMessage[];
  inputTokenCount?: number;
  outputTokenCount?: number;
  elapsedTime?: number;
}
