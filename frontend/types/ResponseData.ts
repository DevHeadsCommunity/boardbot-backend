import { transformKeys } from "@/lib/caseConversion";
import { z } from "zod";
import { ChatMessageSchema } from "./ChatMessage";
import { ProductSchema } from "./Product";

export const ResponseMessageSchema = ChatMessageSchema.extend({
  message: z.object({
    type: z.string(),
    response: z.string(),
    products: z.array(ProductSchema),
    reasoning: z.string(),
    followUpQuestion: z.string(),
    metadata: z.record(z.string(), z.unknown()),
    inputTokenUsage: z.record(z.string(), z.number()),
    outputTokenUsage: z.record(z.string(), z.number()),
    timeTaken: z.record(z.string(), z.number()),
  }),
});

export const ConsistencyTestResultSchema = z.object({
  mainPromptResponse: ResponseMessageSchema,
  variationResponses: z.array(ResponseMessageSchema),
  productConsistency: z.number(),
  orderConsistency: z.number(),
});

export const AccuracyTestResultSchema = z.object({
  response: ResponseMessageSchema,
  productAccuracy: z.number(),
  featureAccuracy: z.number(),
});

export type ResponseMessage = z.infer<typeof ResponseMessageSchema>;
export type ConsistencyTestResult = z.infer<typeof ConsistencyTestResultSchema>;
export type AccuracyTestResult = z.infer<typeof AccuracyTestResultSchema>;

export const responseMessageFromJson = (json: unknown): ResponseMessage => {
  try {
    const camelCaseData = transformKeys(json as Record<string, any>, "snakeToCamel");
    return ResponseMessageSchema.parse(camelCaseData);
  } catch (error) {
    console.error("Error parsing response data:", error);
    throw new Error("Invalid response data");
  }
};

export const responseMessageToJson = (data: ResponseMessage): unknown => {
  return transformKeys(data, "camelToSnake");
};
