export interface ChatMessage {
  id: string;
  timestamp: Date;
  message: string;
  isUserMessage: boolean;
  isComplete: boolean;
  inputTokenCount?: number;
  outputTokenCount?: number;
  elapsedTime?: number;
}
