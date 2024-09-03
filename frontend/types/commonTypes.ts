import { accuracyTestRunnerMachine } from "@/machines/accuracyTestRunnerMachine";
import { consistencyTestRunnerMachine } from "@/machines/consistencyTestRunnerMachine";
import { ActorRefFrom } from "xstate";

// This type is not validated by Zod, but we keep it for type safety in TypeScript
export type TestRunnerRef = ActorRefFrom<typeof accuracyTestRunnerMachine | typeof consistencyTestRunnerMachine>;
