import { Architecture, HistoryManagement, Model, Test, TestCase } from "@/types";
import { ActorRefFrom, assign, ContextFrom, emit, setup } from "xstate";
import { accuracyTestRunnerMachine } from "./accuracyTestRunnerMachine";
import { consistencyTestRunnerMachine } from "./consistencyTestRunnerMachine";

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
  // initial: ({input}) => input?.currentState ? input.currentState : "idle", // This is not working, but we need to find a way to restore the state
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
                const testRunnerMachine = event.data.testType === "accuracy" ? accuracyTestRunnerMachine : consistencyTestRunnerMachine;
                const newTest = {
                  testId: event.data.id,
                  name: event.data.name,
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
                } as Test;
                return [...context.tests, newTest];
              },
            }),
            emit({
              type: "notification",
              data: {
                type: "success",
                message: "Test created successfully",
              },
            }),
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
      testRunnerState: serializeTestRunnerState(test.testRunnerRef),
    })),
    model: snapshot.context.model,
    architecture: snapshot.context.architecture,
    historyManagement: snapshot.context.historyManagement,
    currentState: snapshot.value,
  };
};

export const serializeTestRunnerState = (testRunnerRef: ActorRefFrom<typeof accuracyTestRunnerMachine | typeof consistencyTestRunnerMachine>) => {
  const snapshot = testRunnerRef.getSnapshot();
  return {
    name: snapshot.context.name,
    sessionId: snapshot.context.sessionId,
    testCases: snapshot.context.testCases,
    testResults: snapshot.context.testResults,
    currentTestIndex: snapshot.context.currentTestIndex,
    batchSize: snapshot.context.batchSize,
    testTimeout: snapshot.context.testTimeout,
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
    tests: savedState.tests.map((test: any) => ({
      ...test,
      testRunnerRef: spawn(test.testType === "accuracy" ? accuracyTestRunnerMachine : consistencyTestRunnerMachine, {
        id: test.testId,
        input: deserializeTestRunnerState(test.testRunnerState),
      }),
    })),
  };
};

export const deserializeTestRunnerState = (savedState: any): ContextFrom<typeof accuracyTestRunnerMachine | typeof consistencyTestRunnerMachine> => {
  return {
    webSocketRef: undefined,
    name: savedState.name,
    sessionId: savedState.sessionId,
    testCases: savedState.testCases,
    testResults: savedState.testResults,
    currentTestIndex: savedState.currentTestIndex,
    batchSize: savedState.batchSize,
    testTimeout: savedState.testTimeout,
    progress: savedState.progress,
    model: savedState.model,
    architecture: savedState.architecture,
    historyManagement: savedState.historyManagement,
  };
};
