import { z } from "zod";
import { ProductSchema } from "./Product";

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
