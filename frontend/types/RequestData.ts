export interface RequestData {
  type: string;
  sessionId: string;
  messageId: string;
  message: string;
  timestamp?: string;
  model?: string;
  architectureChoice?: string;
  historyManagementChoice?: string;
}
