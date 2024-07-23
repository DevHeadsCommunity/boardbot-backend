import { FullTestResult, Product, RequestData, ResponseData, TestCase, TestResult } from "@/types";
import { ActorRefFrom, assign, fromPromise, sendTo, setup } from "xstate";
import { Architecture, HistoryManagement, Model } from "./appMachine";
import { webSocketMachine } from "./webSocketMachine";

export function getProductAccuracy(expectedProducts: Product[], actualProducts: Product[]): number {
  if (expectedProducts.length === 0) return 0;

  const correctProducts = expectedProducts.filter((expected, index) => {
    const actual = actualProducts[index];
    return actual && JSON.stringify(expected) === JSON.stringify(actual);
  });

  return correctProducts.length / expectedProducts.length;
}

export function getFeatureAccuracy(expectedProducts: Product[], actualProducts: Product[]): number {
  if (expectedProducts.length === 0) return 0;

  const featureKeys: (keyof Product)[] = [
    "name",
    "size",
    "form",
    "processor",
    "processorTDP",
    "memory",
    "io",
    "manufacturer",
    "operatingSystem",
    "environmental",
    "certifications",
  ];

  let totalFeatures = 0;
  let correctFeatures = 0;

  expectedProducts.forEach((expected, productIndex) => {
    const actual = actualProducts[productIndex];
    if (!actual) return;

    featureKeys.forEach((key) => {
      if (expected[key] !== "NA" && expected[key] !== "") {
        totalFeatures++;
        if (expected[key] === actual[key]) {
          correctFeatures++;
        }
      }
    });
  });

  return totalFeatures > 0 ? correctFeatures / totalFeatures : 0;
}

export const testRunnerMachine = setup({
  types: {
    context: {} as {
      webSocketRef: ActorRefFrom<typeof webSocketMachine> | undefined;
      sessionId: string;
      testCases: TestCase[];
      testResults: TestResult[];
      fullTestResult: FullTestResult | null;
      currentTestIndex: number;
      batchSize: number;
      testTimeout: number;
      progress: number;
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    input: {} as {
      sessionId: string;
      testCases: TestCase[];
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    events: {} as
      | { type: "user.startTest" }
      | { type: "user.pauseTest" }
      | { type: "user.stopTest" }
      | { type: "user.continueTest" }
      | { type: "webSocket.connected" }
      | { type: "webSocket.messageReceived"; data: ResponseData }
      | { type: "webSocket.disconnected" },
  },
  actors: {
    fullTestEvaluator: fromPromise(async ({ input }: { input: { testCases: TestCase[]; testResults: TestResult[] } }) => {
      console.log("===:> fullTestEvaluator", input);
      const { testCases, testResults } = input;
      const averageInputTokenCount = testResults.reduce((acc, result) => acc + result.inputTokenCount, 0) / testResults.length;
      const averageOutputTokenCount = testResults.reduce((acc, result) => acc + result.outputTokenCount, 0) / testResults.length;
      const averageLlmResponseTime = testResults.reduce((acc, result) => acc + result.llmResponseTime, 0) / testResults.length;
      const averageProductAccuracy = testResults.reduce((acc, result) => acc + result.productAccuracy, 0) / testResults.length;
      const averageFeatureAccuracy = testResults.reduce((acc, result) => acc + result.featureAccuracy, 0) / testResults.length;

      return {
        averageInputTokenCount,
        averageOutputTokenCount,
        averageLlmResponseTime,
        averageProductAccuracy,
        averageFeatureAccuracy,
      } as FullTestResult;
    }),
  },
  guards: {
    testIsComplete: ({ context }) => context.currentTestIndex >= context.testCases.length,
  },
}).createMachine({
  context: ({ input }) => ({
    webSocketRef: undefined,
    sessionId: input.sessionId,
    testCases: input.testCases,
    testResults: [],
    fullTestResult: null,
    currentTestIndex: 0,
    batchSize: 1,
    progress: 0,
    testTimeout: 180000,
    model: input.model,
    architecture: input.architecture,
    historyManagement: input.historyManagement,
  }),
  id: "testRunnerActor",
  initial: "idle",
  states: {
    idle: {
      entry: assign({
        webSocketRef: ({ spawn }) => spawn(webSocketMachine) as any,
      }),
      on: {
        "user.startTest": {
          target: "Connecting",
        },
      },
    },
    Connecting: {
      entry: sendTo(
        ({ context }) => context.webSocketRef!,
        ({ context }) => ({
          type: "parentActor.connect",
          data: {
            sessionId: context.sessionId,
          },
        })
      ),
      on: {
        "webSocket.connected": {
          target: "Connected",
        },
      },
    },
    Connected: {
      initial: "RunningBatchTest",
      on: {
        "user.stopTest": {
          target: "Disconnecting",
        },
      },
      states: {
        RunningBatchTest: {
          on: {
            "user.pauseTest": {
              target: "TestPaused",
            },
            "webSocket.messageReceived": [
              {
                target: "EvaluatingFullTestResult",
                actions: assign({
                  testResults: ({ context, event }) => [
                    ...context.testResults,
                    {
                      actualOutput: (event as any).data.textResponse,
                      inputTokenCount: (event as any).data.inputTokenCount,
                      outputTokenCount: (event as any).data.outputTokenCount,
                      llmResponseTime: (event as any).data.elapsedTime,
                      productAccuracy: getProductAccuracy((event as any).data.outputTokenCount, context.testCases[context.currentTestIndex].expectedProducts),
                      featureAccuracy: getFeatureAccuracy((event as any).data.outputTokenCount, context.testCases[context.currentTestIndex].expectedProducts),
                    } as TestResult,
                  ],
                  progress: 100,
                }),
                guard: {
                  type: "testIsComplete",
                },
              },
              {
                target: "RunningBatchTest",
                actions: assign({
                  progress: ({ context }) => (context.currentTestIndex / context.testCases.length) * 100,
                  currentTestIndex: ({ context }) => context.currentTestIndex + 1,
                  testResults: ({ context, event }) => [
                    ...context.testResults,
                    {
                      messageId: (event as any).data.messageId,
                      actualOutput: (event as any).data.textResponse,
                      inputTokenCount: (event as any).data.inputTokenCount,
                      outputTokenCount: (event as any).data.outputTokenCount,
                      llmResponseTime: (event as any).data.elapsedTime,
                      productAccuracy: getProductAccuracy((event as any).data.outputTokenCount, context.testCases[context.currentTestIndex].expectedProducts),
                      featureAccuracy: getFeatureAccuracy((event as any).data.outputTokenCount, context.testCases[context.currentTestIndex].expectedProducts),
                    } as TestResult,
                  ],
                }),
              },
            ],
          },
          entry: [
            sendTo(
              ({ context }) => context.webSocketRef!,
              ({ context }) => {
                return {
                  type: "parentActor.sendMessage",
                  data: {
                    type: "textMessage",
                    sessionId: context.sessionId,
                    messageId: context.testCases[context.currentTestIndex].messageId,
                    message: context.testCases[context.currentTestIndex].input,
                    timestamp: new Date().toISOString(),
                    model: context.model,
                    architectureChoice: context.architecture,
                    historyManagementChoice: context.historyManagement,
                  } as RequestData,
                };
              }
            ),
            assign({
              currentTestIndex: ({ context }) => context.currentTestIndex + 1,
            }),
          ],
        },
        TestPaused: {
          on: {
            "user.continueTest": {
              target: "RunningBatchTest",
            },
          },
        },
        EvaluatingFullTestResult: {
          invoke: {
            id: "fullTestEvaluator",
            input: ({ context }) => {
              return {
                testCases: context.testCases,
                testResults: context.testResults,
              };
            },
            onDone: {
              target: "#testRunnerActor.Disconnecting",
              actions: assign({ fullTestResult: ({ event }) => event.output }),
            },
            src: "fullTestEvaluator",
          },
        },
      },
    },
    Disconnecting: {
      entry: sendTo(({ context }) => context.webSocketRef!, { type: "parentActor.disconnect" }),
      on: {
        "webSocket.disconnected": {
          target: "idle",
        },
      },
    },
  },
});
