import { z } from "zod";

export const MODEL_VALUES = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] as const;
export const ModelSchema = z.enum(MODEL_VALUES);
export type Model = z.infer<typeof ModelSchema>;

export const ARCHITECTURE_VALUES = ["semantic-router", "llm-router", "hybrid-router", "dynamic-agent"] as const;
export const ArchitectureSchema = z.enum(ARCHITECTURE_VALUES);
export type Architecture = z.infer<typeof ArchitectureSchema>;

export const HISTORY_MANAGEMENT_VALUES = ["keep-none", "keep-last-5", "keep-all"] as const;
export const HistoryManagementSchema = z.enum(HISTORY_MANAGEMENT_VALUES);
export type HistoryManagement = z.infer<typeof HistoryManagementSchema>;

export const ChatMessageSchema = z.object({
  sessionId: z.string(),
  messageId: z.string(),
  timestamp: z.date(),
  isUserMessage: z.boolean(),
  isComplete: z.boolean(),
  model: ModelSchema,
  architectureChoice: ArchitectureSchema,
  historyManagementChoice: HistoryManagementSchema,
});

export type ChatMessage = z.infer<typeof ChatMessageSchema>;
