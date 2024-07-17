import { RequestData, ResponseData, Test } from "@/types";
import { assign, sendTo, setup } from "xstate";
import { testRunnerMachine } from "./testRunnerMachine";
import { webSocketMachine } from "./webSocketMachine";

export const testMachine = setup({
  types: {
    context: {} as {
      webSocketRef: null;
      selectedTest: Test | null;
      tests: Test[];
      architectureChoice: string;
      historyManagementChoice: string;
    },
    events: {} as
      | { type: "app.startTest" }
      | { type: "app.stopTest" }
      | { type: "webSocket.disconnected" }
      | { type: "webSocket.connected" }
      | { type: "webSocket.messageReceived", data: ResponseData }
      | { type: "testRunner.sendMessage", data: RequestData }
      | { type: "testRunner.complete" }
      | { type: "user.createTest" }
      | { type: "user.runTest" }
      | { type: "user.pauseTest" }
      | { type: "user.resumeTest" }
      | { type: "user.selectTest", data: Test }
      | { type: "user.clickSingleTestResult" }
      | { type: "user.closeTestResultModal" }
  },
}).createMachine({
  context: {
    webSocketRef: null,
    selectedTest: null,
    tests: [],
    architectureChoice: "semantic-router-v1",
    historyManagementChoice: "keep-all",
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
          actions: sendTo(({ context }) => context.webSocketRef!, {
            type: "parentActor.disconnect",
          } as any),
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
            "user.createTest": {
              target:
                "#testActor.DisplayingTest.Connected.DisplayingTestDetails",
            },
            "user.selectTest": {
              actions: assign({
                selectedTest: ({event, spawn}) => {
                  const selectedTest = event.data;
                  if (!selectedTest.testRunnerRef) {
                    selectedTest.testRunnerRef = spawn(testRunnerMachine);
                  }
                  return selectedTest;
                },
              }),
              target:
                "#testActor.DisplayingTest.Connected.DisplayingTestDetails",
            },
            "webSocket.disconnected": {
              target: "Setup",
            },
          },
          states: {
            DisplayingTestPage: {},
            DisplayingTestDetails: {
              initial: "DisplayingSelectedTest",
              on: {
                "user.runTest": {
                  target:
                    "#testActor.DisplayingTest.Connected.DisplayingTestDetails.RunningTest",
                  actions: sendTo(
                    ({ context }) => context.selectedTest?.testRunnerRef!,
                    {
                      type: "test.startTest",
                    } as any,
                  ),
                },
                "user.clickSingleTestResult": {
                  target:
                    "#testActor.DisplayingTest.Connected.DisplayingTestDetails.DisplayingTestDetailsModal",
                },
              },
              states: {
                DisplayingSelectedTest: {},
                RunningTest: {
                  on: {
                    "user.pauseTest": {
                      actions: sendTo(
                        ({ context }) => context.selectedTest?.testRunnerRef!,
                        {
                          type: "test.pauseTest",
                        } as any,
                      ),
                    },
                    "user.resumeTest": {
                      actions: sendTo(
                        ({ context }) => context.selectedTest?.testRunnerRef!,
                        {
                          type: "test.resumeTest",
                        } as any,
                      ),
                    },
                    "testRunner.complete": {
                      target: "DisplayingSelectedTest",
                    },
                    "testRunner.sendMessage": {
                      actions: sendTo(
                          ({ context }) => context.webSocketRef!,
                          ({ context, event }) => {
                            return {
                              type: "webSocket.sendMessage",
                              data: {
                                type: "textMessage",
                                sessionId: context.selectedTest?.sessionId,
                                messageId: (event as any).webSocketRef?.messageId,
                                message: (event as any).data.message,
                                architectureChoice: (event as any).architectureChoice,
                                historyManagementChoice: (event as any).historyManagementChoice,
                            } as RequestData
                          }
                        }) as any,
                    },
                    "webSocket.messageReceived": {
                      actions: sendTo(
                          ({ context }) => context.selectedTest?.testRunnerRef!,
                          ({ context, event }) => {
                            return {
                              type: "testRunner.messageResponse",
                              data: {
                                type: "textMessage",
                                sessionId: context.selectedTest?.sessionId,
                                messageId: (event as any).data.messageId,
                                textResponse: (event as any).data.textResponse,
                                isComplete: (event as any).data.isComplete,
                                inputTokenCount: (event as any).data.inputTokenCount,
                                outputTokenCount: (event as any).data.outputTokenCount,
                                elapsedTime: (event as any).data.elapsedTime,
                              } as ResponseData
                          }
                        }) as any,
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
    },
  },
});
