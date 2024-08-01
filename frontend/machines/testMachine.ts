import { Test, TestCase } from "@/types";
import { ActorRefFrom, assign, emit, setup } from "xstate";
import { Architecture, HistoryManagement, Model } from "./appMachine";
import { testRunnerMachine } from "./testRunnerMachine";

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
      | { type: "user.createTest"; data: { name: string; id: string; testCase: TestCase[]; createdAt: string } }
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
  states: {
    idle: {
      on: {
        "app.startTest": {
          target: "DisplayingTest",
        },
      },
    },
    DisplayingTest: {
      initial: "DisplayingTestPage",
      on: {
        "user.createTest": {
          target: "#testActor.DisplayingTest.DisplayingTestDetails",
          actions: [
            assign({
              tests: ({ context, event, spawn }) => {
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
          target: "#testActor.DisplayingTest.DisplayingTestDetails",
          actions: assign({
            selectedTest: ({ context, event }) => context.tests.find((test) => test.testId === event.data.testId) || null,
          }),
        },
        "app.stopTest": {
          target: "idle",
        },
      },
      states: {
        DisplayingTestPage: {},
        DisplayingTestDetails: {
          initial: "DisplayingSelectedTest",
          states: {
            DisplayingSelectedTest: {
              on: {
                "user.clickSingleTestResult": {
                  target: "DisplayingTestDetailsModal",
                },
              },
            },
            DisplayingTestDetailsModal: {
              on: {
                "user.closeTestResultModal": {
                  target: "DisplayingSelectedTest",
                },
              },
            },
          },
        },
      },
    },
  },
});

export const getTestMachineState = (testRef: ActorRefFrom<typeof testMachine>) => {
  const snapshot = testRef.getSnapshot();
  return {
    selectedTest: snapshot.context.selectedTest,
    tests: snapshot.context.tests,
    model: snapshot.context.model,
    architecture: snapshot.context.architecture,
    historyManagement: snapshot.context.historyManagement,
    currentState: snapshot.value,
  };
};
