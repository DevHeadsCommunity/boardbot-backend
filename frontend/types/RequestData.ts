import { transformKeys } from "@/lib/caseConversion";
import { z } from "zod";
import { ChatMessageSchema } from "./ChatMessage";

export const RequestDataSchema = ChatMessageSchema.extend({
  type: z.string(),
  sessionId: z.string(),
  messageId: z.string(),
  message: z.string(),
  timestamp: z.string().optional(),
  model: z.string().optional(),
  architectureChoice: z.string().optional(),
  historyManagementChoice: z.string().optional(),
});

export type RequestData = z.infer<typeof RequestDataSchema>;

export const requestDataFromJson = (json: unknown): RequestData => {
  const camelCaseData = transformKeys(json as Record<string, any>, "snakeToCamel");
  return RequestDataSchema.parse(camelCaseData);
};

export const requestDataToJson = (data: RequestData): unknown => {
  return transformKeys(data, "camelToSnake");
};
