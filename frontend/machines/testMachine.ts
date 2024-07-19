import { RequestData, ResponseData, Test, TestCase } from "@/types";
import { ActorRefFrom, assign, emit, sendTo, setup } from "xstate";
import { testRunnerMachine } from "./testRunnerMachine";
import { webSocketMachine } from "./webSocketMachine";

export const testMachine = setup({
  types: {
    context: {} as {
      webSocketRef: ActorRefFrom<typeof webSocketMachine> | undefined;
      selectedTest: Test | null;
      tests: Test[];
    },
    events: {} as
      | { type: "app.startTest" }
      | { type: "app.stopTest" }
      | { type: "webSocket.connected" }
      | { type: "webSocket.messageReceived"; data: ResponseData }
      | { type: "webSocket.disconnected" }
      | { type: "testRunner.startTest" }
      | { type: "testRunner.sendMessage"; data: RequestData }
      | { type: "testRunner.complete" }
      | { type: "user.createTest"; data: { name: string; id: string; testCase: TestCase; createdAt: string } }
      | { type: "user.selectTest"; data: Test }
      | { type: "user.clickSingleTestResult" }
      | { type: "user.closeTestResultModal" },
  },
}).createMachine({
  context: {
    webSocketRef: undefined,
    selectedTest: null,
    tests: [],
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
              target: "#testActor.DisplayingTest.Connected.DisplayingTestDetails",
              actions: [
                assign({
                  tests: ({ context, event, spawn }) => {
                    const newTest = {
                      id: event.data.id,
                      name: event.data.name,
                      createdAt: event.data.createdAt,
                      sessionId: event.data.testCase.id,
                      testRunnerRef: spawn(testRunnerMachine),
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
              target: "#testActor.DisplayingTest.Connected.DisplayingTestDetails",
              actions: assign({
                selectedTest: ({ event, spawn }) => {
                  const selectedTest = event.data;
                  if (!selectedTest.testRunnerRef) {
                    selectedTest.testRunnerRef = spawn(testRunnerMachine);
                  }
                  return selectedTest;
                },
              }),
            },
            "webSocket.disconnected": {
              target: "Setup",
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
                    "testRunner.startTest": {
                      target: "RunningTest",
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
                RunningTest: {
                  on: {
                    "testRunner.complete": {
                      target: "DisplayingSelectedTest",
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
                            } as ResponseData,
                          };
                        }
                      ) as any,
                    },
                    "testRunner.sendMessage": {
                      actions: sendTo(
                        ({ context }) => context.webSocketRef!,
                        ({ context, event }) => {
                          return {
                            type: "parentActor.sendMessage",
                            data: {
                              type: "textMessage",
                              sessionId: context.selectedTest?.sessionId,
                              messageId: (event as any).webSocketRef?.messageId,
                              message: (event as any).data.message,
                              architectureChoice: (event as any).data.architectureChoice,
                              historyManagementChoice: (event as any).data.historyManagementChoice,
                            } as RequestData,
                          };
                        }
                      ) as any,
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
