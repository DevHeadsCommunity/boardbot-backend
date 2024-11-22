import {
  AccuracyTestResultSchema,
  Architecture,
  ConsistencyTestResultSchema,
  ContextRetentionTestResultSchema,
  ConversationalFlowTestResultSchema,
  DefensibilityTestResultSchema,
  FeatureInferenceTestResultSchema,
  HistoryManagement,
  Model,
  RobustnessTestResultSchema,
  Test,
  TestCase,
} from "@/types";
import { ActorRefFrom, assign, ContextFrom, emit, setup } from "xstate";
import { z } from "zod";
import { accuracyTestRunnerMachine } from "./accuracyTestRunnerMachine";
import { consistencyTestRunnerMachine } from "./consistencyTestRunnerMachine";
import { contextRetentionTestRunnerMachine } from "./contextRetentionTestRunnerMachine";
import { conversationalFlowTestRunnerMachine } from "./conversationalFlowTestRunnerMachine";
import { defensibilityTestRunnerMachine } from "./defensibilityTestRunnerMachine";
import { featureInferenceTestRunnerMachine } from "./featureInferenceTestRunnerMachine";
import { robustnessTestRunnerMachine } from "./robustnessTestRunnerMachine";

export const testMachine = setup({
  types: {
    context: {} as {
      selectedTest: Test | null;
      tests: Test[];
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    input: {} as {
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
      restoredState?: any;
    },
    events: {} as
      | { type: "app.startTest" }
      | { type: "app.stopTest" }
      | { type: "app.updateState"; data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement } }
      | { type: "user.createTest"; data: { testType: string; name: string; id: string; testCase: TestCase[]; createdAt: string } }
      | { type: "user.selectTest"; data: { testId: string } }
      | { type: "user.clickSingleTestResult" }
      | { type: "user.closeTestResultModal" },
  },
}).createMachine({
  context: ({ input }) => ({
    selectedTest: input.restoredState?.selectedTest || null,
    tests: input.restoredState?.tests || [],
    model: input.model,
    architecture: input.architecture,
    historyManagement: input.historyManagement,
  }),
  id: "testActor",
  initial: "idle",
  on: {
    "app.updateState": {
      actions: assign({
        model: ({ event }) => event.data.model,
        architecture: ({ event }) => event.data.architecture,
        historyManagement: ({ event }) => event.data.historyManagement,
      }),
    },
  },
  states: {
    idle: {
      on: {
        "app.startTest": {
          target: "displayingTest",
        },
      },
    },
    displayingTest: {
      initial: "displayingTestPage",
      on: {
        "user.createTest": {
          target: "#testActor.displayingTest.displayingTestDetails",
          actions: [
            assign({
              tests: ({ context, event, spawn }) => {
                let testRunnerMachine;
                switch (event.data.testType) {
                  case "accuracy":
                    testRunnerMachine = accuracyTestRunnerMachine;
                    break;
                  case "consistency":
                    testRunnerMachine = consistencyTestRunnerMachine;
                    break;
                  case "feature_inference":
                    testRunnerMachine = featureInferenceTestRunnerMachine;
                    break;
                  case "context_retention":
                    testRunnerMachine = contextRetentionTestRunnerMachine;
                    break;
                  case "robustness":
                    testRunnerMachine = robustnessTestRunnerMachine;
                    break;
                  case "conversational_flow":
                    testRunnerMachine = conversationalFlowTestRunnerMachine;
                    break;
                  case "defensibility":
                    testRunnerMachine = defensibilityTestRunnerMachine;
                    break;
                  default:
                    throw new Error(`Unknown test type: ${event.data.testType}`);
                }

                const newTest: Test = {
                  testId: event.data.id,
                  name: event.data.name,
                  testType: event.data.testType,
                  createdAt: event.data.createdAt,
                  testRunnerRef: spawn(testRunnerMachine, {
                    input: {
                      name: event.data.name,
                      sessionId: event.data.id,
                      testCases: event.data.testCase,
                      model: context.model,
                      architecture: context.architecture,
                      historyManagement: context.historyManagement,
                    },
                  }),
                };

                return [...context.tests, newTest];
              },
            }),
            // emit({
            //   type: "notification",
            //   data: {
            //     type: "success",
            //     message: "Test created successfullyZ344",
            //   },
            // }),
          ],
        },
        "user.selectTest": {
          target: "#testActor.displayingTest.displayingTestDetails",
          actions: assign({
            selectedTest: ({ context, event }) => context.tests.find((test) => test.testId === event.data.testId) || null,
          }),
        },
        "app.stopTest": {
          target: "idle",
        },
      },
      states: {
        displayingTestPage: {},
        displayingTestDetails: {
          initial: "displayingSelectedTest",
          states: {
            displayingSelectedTest: {
              on: {
                "user.clickSingleTestResult": {
                  target: "displayingTestDetailsModal",
                },
              },
            },
            displayingTestDetailsModal: {
              on: {
                "user.closeTestResultModal": {
                  target: "displayingSelectedTest",
                },
              },
            },
          },
        },
      },
    },
  },
});

export const serializeTestState = (testRef: ActorRefFrom<typeof testMachine>) => {
  const snapshot = testRef.getSnapshot();
  return {
    selectedTest: snapshot.context.selectedTest,
    tests: snapshot.context.tests.map((test) => ({
      ...test,
      testRunnerState: serializeTestRunnerState(test.testRunnerRef, test.testType),
    })),
    model: snapshot.context.model,
    architecture: snapshot.context.architecture,
    historyManagement: snapshot.context.historyManagement,
    currentState: snapshot.value,
  };
};

export const serializeTestRunnerState = (
  testRunnerRef: ActorRefFrom<
    | typeof accuracyTestRunnerMachine
    | typeof consistencyTestRunnerMachine
    | typeof featureInferenceTestRunnerMachine
    | typeof contextRetentionTestRunnerMachine
    | typeof robustnessTestRunnerMachine
    | typeof conversationalFlowTestRunnerMachine
    | typeof defensibilityTestRunnerMachine
  >,
  testType: string
) => {
  const snapshot = testRunnerRef.getSnapshot();
  return {
    name: snapshot.context.name,
    sessionId: snapshot.context.sessionId,
    testCases: snapshot.context.testCases,
    testResults: snapshot.context.testResults,
    currentTestIndex: snapshot.context.currentTestIndex,
    progress: snapshot.context.progress,
    model: snapshot.context.model,
    architecture: snapshot.context.architecture,
    historyManagement: snapshot.context.historyManagement,
    currentState: snapshot.value,
  };
};

export const deserializeTestState = (savedState: any, spawn: any): ContextFrom<typeof testMachine> => {
  return {
    ...savedState,
    tests: savedState.tests.map((test: any) => {
      let testRunnerMachine;
      switch (test.testType) {
        case "accuracy":
          testRunnerMachine = accuracyTestRunnerMachine;
          break;
        case "consistency":
          testRunnerMachine = consistencyTestRunnerMachine;
          break;
        case "feature_inference":
          testRunnerMachine = featureInferenceTestRunnerMachine;
          break;
        case "context_retention":
          testRunnerMachine = contextRetentionTestRunnerMachine;
          break;
        case "robustness":
          testRunnerMachine = robustnessTestRunnerMachine;
          break;
        case "conversational_flow":
          testRunnerMachine = conversationalFlowTestRunnerMachine;
          break;
        case "defensibility":
          testRunnerMachine = defensibilityTestRunnerMachine;
          break;
        default:
          throw new Error(`Unknown test type: ${test.testType}`);
      }

      return {
        ...test,
        testRunnerRef: spawn(testRunnerMachine, {
          id: test.testId,
          input: deserializeTestRunnerState(test.testRunnerState, test.testType),
        }),
      };
    }),
  };
};

export const deserializeTestRunnerState = (savedState: any, testType: string): any => {
  const baseState = {
    webSocketRef: undefined,
    name: savedState.name,
    sessionId: savedState.sessionId,
    testCases: savedState.testCases,
    currentTestIndex: savedState.currentTestIndex,
    progress: savedState.progress,
    model: savedState.model,
    architecture: savedState.architecture,
    historyManagement: savedState.historyManagement,
  };

  switch (testType) {
    case "accuracy":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(AccuracyTestResultSchema).parse(savedState.testResults) : [],
      };
    case "consistency":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(ConsistencyTestResultSchema).parse(savedState.testResults) : [],
        pendingResponses: savedState.pendingResponses || 0,
        currentResponses: savedState.currentResponses || [],
      };
    case "feature_inference":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(FeatureInferenceTestResultSchema).parse(savedState.testResults) : [],
      };
    case "context_retention":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(ContextRetentionTestResultSchema).parse(savedState.testResults) : [],
        conversation: savedState.conversation || [],
      };
    case "robustness":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(RobustnessTestResultSchema).parse(savedState.testResults) : [],
      };
    case "conversational_flow":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(ConversationalFlowTestResultSchema).parse(savedState.testResults) : [],
        conversation: savedState.conversation || [],
      };
    case "defensibility":
      return {
        ...baseState,
        testResults: savedState.testResults ? z.array(DefensibilityTestResultSchema).parse(savedState.testResults) : [],
        conversation: savedState.conversation || [],
      };
    default:
      throw new Error(`Unknown test type: ${testType}`);
  }
};
