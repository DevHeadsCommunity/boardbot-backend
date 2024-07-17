export interface RequestData {
  type: string;
  sessionId: string;
  id: string;
  message: string;
  architecture?: string;
  chatHistoryManagementChoice?: string;
}
