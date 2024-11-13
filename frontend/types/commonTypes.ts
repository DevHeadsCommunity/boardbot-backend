import {
  accuracyTestRunnerMachine,
  consistencyTestRunnerMachine,
  contextRetentionTestRunnerMachine,
  conversationalFlowTestRunnerMachine,
  defensibilityTestRunnerMachine,
  featureInferenceTestRunnerMachine,
  robustnessTestRunnerMachine,
} from "@/machines";
import { ActorRefFrom } from "xstate";

// This type is not validated by Zod, but we keep it for type safety in TypeScript
export type TestRunnerRef = ActorRefFrom<
  | typeof accuracyTestRunnerMachine
  | typeof consistencyTestRunnerMachine
  | typeof featureInferenceTestRunnerMachine
  | typeof contextRetentionTestRunnerMachine
  | typeof robustnessTestRunnerMachine
  | typeof conversationalFlowTestRunnerMachine
  | typeof defensibilityTestRunnerMachine
>;
