import { Test, TestCase, TestResult } from "@/types";
import { assign, sendTo, setup } from "xstate";

export const machine = setup({
  types: {
    context: {} as {
      webSocketRef: null;
      currentTest: Test | null;
      testCases: TestCase[];
      results: TestResult[];
      currentTestIndex: number;
      progress: number;
      batchSize: number;
      resTimeOut: number;
      architecture: string;
      chatHistoryManagmentChoice: string;
    },
    events: {} as
      | { type: "app.startTest" }
      | { type: "user.startTest" }
      | { type: "user.pauseTest" }
      | { type: "user.resumeTest" }
      | { type: "user.retryFailedTests" }
      | { type: "webSocket.disconnected" }
      | { type: "app.stopTest" }
      | { type: "webSocket.connected" }
      | { type: "user.createTest" }
      | { type: "user.selectTest" }
      | { type: "testRunner.complete" }
      | { type: "evaluator.complete" }
      | { type: "user.updateSetting" }
      | { type: "update.complete" }
      | { type: "user.importState" }
      | { type: "user.exportState" }
      | { type: "user.clickSingleTestResult" }
      | { type: "user.closeTestResultModal" },
  },
  actors: {
    testRunner: createMachine({
      /* ... */
    }),
  },
  guards: {
    testComplete: function ({ context, event }) {
      // Add your guard condition here
      return true;
    },
  },
}).createMachine({
  context: {
    webSocketRef: null,
    currentTest: null,
    testCases: [],
    results: [],
    currentTestIndex: 0,
    progress: 0,
    batchSize: 10,
    resTimeOut: 1000,
    architecture: "agentic",
    chatHistoryManagmentChoice: "1",
  },
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
      initial: "Setup",
      on: {
        "app.stopTest": {
          target: "idle",
          actions: [
            sendTo(({ context }) => context.webSocketRef!, {
              type: "parentActor.disconnect",
            } as any),
            assign({
              currentTest: null,
              testCases: [],
              results: [],
              currentTestIndex: 0,
              progress: 0,
              status: "PENDING" as const,
            }),
          ],
        },
        "webSocket.connected": {
          target: "#testActor.DisplayingTest.Connected",
        },
      },
      entry: assign({
        webSocketRef: ({ spawn }) => spawn(webSocketMachine) as any,
      }),
      states: {
        Setup: {},
        Connected: {
          initial: "DisplayingTestPage",
          on: {
            "webSocket.disconnected": {
              target: "Setup",
            },
            "user.updateSetting": {
              target: "#testActor.DisplayingTest.Connected.UpdattingSettings",
            },
            "user.exportState": {
              target: "#testActor.DisplayingTest.Connected.ExportingState",
            },
            "user.importState": {
              target: "#testActor.DisplayingTest.Connected.ImportingState",
            },
            "user.clickSingleTestResult": {
              target:
                "#testActor.DisplayingTest.Connected.DisplayingTestDetailsModal",
            },
          },
          states: {
            DisplayingTestPage: {
              on: {
                "user.createTest": {
                  target: "TestReady",
                },
                "user.selectTest": {
                  target: "TestReady",
                },
              },
            },
            TestReady: {
              on: {
                "user.startTest": {
                  target: "RunningTest",
                  actions: assign({ status: "RUNNING" as const }),
                },
              },
            },
            RunningTest: {
              initial: "RunningTestBatch",
              on: {
                "user.pauseTest": {
                  target: "TestPaused",
                  actions: assign({ status: "PAUSED" as const }),
                },
              },
              states: {
                RunningTestBatch: {
                  on: {
                    "testRunner.complete": {
                      target: "EvaluateBatchResult",
                    },
                  },
                  invoke: {
                    input: {},
                    src: "testRunner",
                  },
                },
                EvaluateBatchResult: {
                  on: {
                    "evaluator.complete": [
                      {
                        target:
                          "#testActor.DisplayingTest.Connected.TestCompleted",
                        guard: {
                          type: "testComplete",
                        },
                      },
                      {
                        target: "RunningTestBatch",
                      },
                    ],
                  },
                },
              },
            },
            TestPaused: {
              on: {
                "user.resumeTest": {
                  target: "RunningTest",
                  actions: assign({ status: "RUNNING" as const }),
                },
              },
            },
            TestCompleted: {
              on: {
                "user.retryFailedTests": {
                  target: "RunningTest",
                  actions: assign({
                    testCases: ({ context }) =>
                      context.results
                        .filter((result) => !result.isCorrect)
                        .map((result) => result as TestCase),
                    results: ({ context }) =>
                      context.results.filter((result) => result.isCorrect),
                    currentTestIndex: 0,
                    progress: 0,
                    status: "RUNNING" as const,
                  }),
                },
              },
              entry: assign({ status: "COMPLETED" as const }),
            },
            UpdattingSettings: {
              on: {
                "update.complete": {
                  target: "DisplayingTestPage",
                },
              },
            },
            ExportingState: {},
            ImportingState: {},
            DisplayingTestDetailsModal: {
              on: {
                "user.closeTestResultModal": {
                  target: "#testActor.DisplayingTest.Connected",
                },
              },
            },
          },
        },
      },
    },
  },
});
