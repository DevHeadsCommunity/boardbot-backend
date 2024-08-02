import { FullTestResult, Product, RequestData, ResponseData, TestCase, TestResult } from "@/types";
import { ActorRefFrom, assign, fromPromise, sendTo, setup } from "xstate";
import { Architecture, HistoryManagement, Model } from "./appMachine";
import { webSocketMachine } from "./webSocketMachine";

function parseActualProducts(actualProducts: string | Product[]): Product[] {
  console.log("===:> actualProducts p", actualProducts);
  if (typeof actualProducts === "string") {
    try {
      return JSON.parse(actualProducts)["products"];
    } catch (error) {
      console.error("Error parsing expectedProducts:", error);
      return [];
    }
  }
  return actualProducts;
}

export function getProductAccuracy(actualProducts: string | Product[], expectedProducts: Product[]): number {
  const parsedActualProducts = parseActualProducts(actualProducts);
  console.log("===:> parsedActualProducts", parsedActualProducts);
  console.log("===:> expectedProducts", expectedProducts);

  if (parsedActualProducts.length === 0) return 0;

  const correctProducts = parsedActualProducts.filter((actual, index) => {
    const expected = expectedProducts[index];
    return actual && expected.name.toLowerCase() === actual.name.toLowerCase();
  });

  return correctProducts.length / parsedActualProducts.length;
}

export function getFeatureAccuracy(actualProducts: string | Product[]): number {
  const parsedActualProducts = parseActualProducts(actualProducts);

  if (parsedActualProducts.length === 0) return 0;

  const features: (keyof Product)[] = ["name", "size", "form", "processor", "processorTDP", "memory", "io", "manufacturer", "operatingSystem", "environmental", "certifications"];

  const featureAccuracy = parsedActualProducts.reduce((acc, actual) => {
    const expectedFeatures = Object.keys(actual);
    const correctFeatures = expectedFeatures.filter((feature) => features.includes(feature as keyof Product));
    const correctFeaturesCount = correctFeatures.length;
    const totalFeaturesCount = expectedFeatures.length;
    return acc + correctFeaturesCount / totalFeaturesCount;
  }, 0);

  return featureAccuracy / parsedActualProducts.length;
}

export const testRunnerMachine = setup({
  types: {
    context: {} as {
      webSocketRef: ActorRefFrom<typeof webSocketMachine> | undefined;
      name: string;
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
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: TestResult[];
      fullTestResult?: FullTestResult;
      currentTestIndex?: number;
      batchSize?: number;
      testTimeout?: number;
      Progress?: number;
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
  actions: {
    sendNextMessage: sendTo(
      ({ context }) => context.webSocketRef!,
      ({ context }) => ({
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
      })
    ),
    updateTestResults: assign({
      testResults: ({ context, event }) => {
        const currentTest = context.testCases[context.currentTestIndex - 1];
        console.log("Current test case:", currentTest);
        console.log("Expected products:", currentTest.expectedProducts);
        console.log("Actual products:", (event as any).data.textResponse);
        console.log("Data:", (event as any).data);

        return [
          ...context.testResults,
          {
            messageId: (event as any).data.messageId.replace("_response", ""),
            actualOutput: (event as any).data.message,
            inputTokenCount: (event as any).data.inputTokenCount,
            outputTokenCount: (event as any).data.outputTokenCount,
            llmResponseTime: (event as any).data.elapsedTime,
            productAccuracy: getProductAccuracy((event as any).data.message, currentTest.expectedProducts),
            featureAccuracy: getFeatureAccuracy((event as any).data.message),
          } as TestResult,
        ];
      },
    }),
    increaseProgress: assign({
      progress: ({ context }) => (context.currentTestIndex / context.testCases.length) * 100,
    }),
    increaseCurrentTestIndex: assign({
      currentTestIndex: ({ context }) => context.currentTestIndex + 1,
    }),
  },
  guards: {
    testIsComplete: ({ context }) => {
      console.log("===:> testIsComplete", context.currentTestIndex, context.testCases.length);
      return context.currentTestIndex >= context.testCases.length;
    },
  },
}).createMachine({
  context: ({ input }) => ({
    webSocketRef: undefined,
    name: input.name,
    sessionId: input.sessionId,
    testCases: input.testCases,
    testResults: input?.testResults || [],
    fullTestResult: input?.fullTestResult || null,
    currentTestIndex: input?.currentTestIndex || 0,
    batchSize: input?.batchSize || 1,
    progress: input?.Progress || 0,
    testTimeout: input?.testTimeout || 10000,
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
          entry: [
            "sendNextMessage",
            "increaseCurrentTestIndex",
            ({ context, event }) => {
              console.log("===:> RunningBatchTest", event);
            },
          ],
          on: {
            "user.pauseTest": {
              target: "TestPaused",
            },
            "webSocket.messageReceived": [
              {
                target: "EvaluatingFullTestResult",
                actions: [
                  ({ context, event }) => {
                    console.log("===:> webSocket.messageReceived: if", event);
                  },
                  "updateTestResults",
                  "increaseProgress",
                ],
                guard: {
                  type: "testIsComplete",
                },
              },
              {
                target: "RunningBatchTest",
                actions: [
                  ({ context, event }) => {
                    console.log("===:> webSocket.messageReceived: else", event);
                  },
                  "sendNextMessage",
                  "increaseCurrentTestIndex",
                  "updateTestResults",
                  "increaseProgress",
                ],
              },
            ],
          },
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
