import { accuracyTestRunnerMachine } from "@/machines/accuracyTestRunnerMachine";
import { consistencyTestRunnerMachine } from "@/machines/consistencyTestRunnerMachine";
import { ActorRefFrom } from "xstate";
import { z } from "zod";

// const TestRunnerRefSchema = z.custom<TestRunnerRef>((val) => typeof val === 'object' && val !== null && 'send' in val && 'subscribe' in val);

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

// This type is not validated by Zod, but we keep it for type safety in TypeScript
export type TestRunnerRef = ActorRefFrom<typeof accuracyTestRunnerMachine | typeof consistencyTestRunnerMachine>;
