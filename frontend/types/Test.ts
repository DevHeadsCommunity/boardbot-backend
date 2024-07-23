import { testRunnerMachine } from "@/machines/testRunnerMachine";
import { ActorRefFrom } from "xstate";

export interface Test {
  testId: string; // would be used as sessionId
  name: string;
  createdAt: string;
  testRunnerRef: ActorRefFrom<typeof testRunnerMachine>;
  startTimestamp?: number;
  endTimestamp?: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
