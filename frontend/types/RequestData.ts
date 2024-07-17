export interface RequestData {
  type: string;
  sessionId: string;
  messageId: string;
  message: string;
  architectureChoice?: string;
  historyManagementChoice?: string;
}
