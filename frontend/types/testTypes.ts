import { z } from "zod";
import { ResponseMessageSchema } from "./chatTypes";
import { ProductSchema } from "./productTypes";

export const TEST_TYPES = ["accuracy", "consistency"] as const;
export const TestTypeSchema = z.enum(TEST_TYPES);
export type TestType = z.infer<typeof TestTypeSchema>;

export const TestCaseSchema = z.object({
  messageId: z.string(),
  input: z.string(),
  testType: TestTypeSchema,
  expectedProducts: z.array(ProductSchema).optional(),
  variations: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  tags: z.array(z.string()).optional(),
});

export type TestCase = z.infer<typeof TestCaseSchema>;

export const TestSchema = z.object({
  testId: z.string(),
  name: z.string(),
  createdAt: z.string(),
  testRunnerRef: z.any(), // We can't directly validate XState ActorRefs with Zod
  startTimestamp: z.number().optional(),
  endTimestamp: z.number().optional(),
  error: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type Test = z.infer<typeof TestSchema>;

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

export type ConsistencyTestResult = z.infer<typeof ConsistencyTestResultSchema>;
export type AccuracyTestResult = z.infer<typeof AccuracyTestResultSchema>;
