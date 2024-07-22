export interface RequestData {
  type: string;
  sessionId: string;
  messageId: string;
  message: string;
  model?: string;
  architectureChoice?: string;
  historyManagementChoice?: string;
}
