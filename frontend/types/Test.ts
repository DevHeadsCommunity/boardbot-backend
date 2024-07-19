import { testRunnerMachine } from "@/machines/testRunnerMachine";
import { ActorRefFrom } from "xstate";

export interface Test {
  id: string;
  name: string;
  createdAt: string;
  sessionId: string;
  testRunnerRef: ActorRefFrom<typeof testRunnerMachine>
  startTimestamp?: number;
  endTimestamp?: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
