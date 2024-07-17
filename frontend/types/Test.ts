import { ActorRef } from "xstate";

export interface Test {
  id: string;
  name: string;
  createdAt: string;
  sessionId: string;
  testRunnerRef: ActorRef<any, any>;
  startTimestamp?: number;
  endTimestamp?: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
