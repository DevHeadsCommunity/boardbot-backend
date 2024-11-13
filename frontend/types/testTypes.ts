import { z } from "zod";
import { ResponseMessageSchema } from "./chatTypes";
import { ExpectedProductSchema } from "./productTypes";

// Test Types Enum
export const TEST_TYPES = ["accuracy", "consistency", "feature_inference", "context_retention", "robustness", "conversational_flow", "defensibility"] as const;

export const TestTypeSchema = z.enum(TEST_TYPES);
export type TestType = z.infer<typeof TestTypeSchema>;

// Base Test Case Schema
export const TestCaseSchema = z.object({
  messageId: z.string(),
  prompt: z.string(),
  testType: TestTypeSchema,
  description: z.string(),
  products: z.array(ExpectedProductSchema).optional(),
  variations: z.array(z.string()).optional(),
  conversation: z
    .array(
      z.object({
        turn: z.number(),
        query: z.string(),
        expected_filters: z.record(z.any()).optional(),
        message: z.string().optional(),
      })
    )
    .optional(),
  expected_filters: z.record(z.any()).optional(),
  category: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  tags: z.array(z.string()).optional(),
});

export type TestCase = z.infer<typeof TestCaseSchema>;

// Test Schema (maintains existing structure)
export const TestSchema = z.object({
  testId: z.string(),
  name: z.string(),
  testType: TestTypeSchema,
  createdAt: z.string(),
  testRunnerRef: z.any(), // We can't directly validate XState ActorRefs with Zod
  startTimestamp: z.number().optional(),
  endTimestamp: z.number().optional(),
  error: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type Test = z.infer<typeof TestSchema>;

// Test Result Schemas
export const AccuracyTestResultSchema = z.object({
  response: ResponseMessageSchema,
  productAccuracy: z.number(),
});

export const ConsistencyTestResultSchema = z.object({
  mainPromptResponse: ResponseMessageSchema,
  variationResponses: z.array(ResponseMessageSchema),
  productConsistency: z.number(),
  orderConsistency: z.number(),
});

export const FeatureInferenceTestResultSchema = z.object({
  response: ResponseMessageSchema,
  filterAccuracy: z.number(),
  extractedFilters: z.record(z.any()),
  expectedFilters: z.record(z.any()),
});

export const ContextRetentionTestResultSchema = z.object({
  conversation: z.array(ResponseMessageSchema),
  contextAccuracy: z.number(),
  filterProgression: z.array(z.record(z.any())),
});

export const RobustnessTestResultSchema = z.object({
  response: ResponseMessageSchema,
  filterAccuracy: z.number(),
  noiseFiltering: z.number(),
  extractedFilters: z.record(z.any()),
});

export const ConversationalFlowTestResultSchema = z.object({
  conversation: z.array(ResponseMessageSchema),
  flowCoherence: z.number(),
  topicTransitionAccuracy: z.number(),
});

export const DefensibilityTestResultSchema = z.object({
  conversation: z.array(ResponseMessageSchema),
  boundaryMaintenance: z.number(),
  appropriateResponse: z.boolean(),
});

// Type exports
export type AccuracyTestResult = z.infer<typeof AccuracyTestResultSchema>;
export type ConsistencyTestResult = z.infer<typeof ConsistencyTestResultSchema>;
export type FeatureInferenceTestResult = z.infer<typeof FeatureInferenceTestResultSchema>;
export type ContextRetentionTestResult = z.infer<typeof ContextRetentionTestResultSchema>;
export type RobustnessTestResult = z.infer<typeof RobustnessTestResultSchema>;
export type ConversationalFlowTestResult = z.infer<typeof ConversationalFlowTestResultSchema>;
export type DefensibilityTestResult = z.infer<typeof DefensibilityTestResultSchema>;
