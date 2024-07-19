import { FullTestResult, Product, RequestData, ResponseData, TestCase, TestResult } from "@/types";
import { assign, fromPromise, sendParent, setup } from "xstate";


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
    "name", "size", "form", "processor", "processorTDP", "memory", "io",
    "manufacturer", "operatingSystem", "environmental", "certifications"
  ];

  let totalFeatures = 0;
  let correctFeatures = 0;

  expectedProducts.forEach((expected, productIndex) => {
    const actual = actualProducts[productIndex];
    if (!actual) return;

    featureKeys.forEach(key => {
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
      testCases: TestCase[];
      testResults: TestResult[];
      fullTestResult: FullTestResult| null;
      currentTestIndex: number;
      batchSize: number;
      testTimeout: number;
      progress: number;
    },
    events: {} as
      | { type: "test.messageReceived", data: ResponseData }
      | { type: "user.startTest" }
      | { type: "user.stopTest" }
      | { type: "user.continueTest" }
      | { type: "user.pauseTest" },
  },
  actors: {
    fullTestEvaluator: fromPromise( async ({input}: {input: {testCases: TestCase[], testResults: TestResult[]}}) => {
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
  context: {
    testCases: [],
    testResults: [],
    fullTestResult: null,
    currentTestIndex: 0,
    batchSize: 1,
    progress: 0,
    testTimeout: 180000,
  },
  id: "testRunnerActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "user.startTest": {
          target: "RunningTest",
        },
      },
    },
    RunningTest: {
      initial: "RunningBatchTest",
      on: {
        "user.stopTest": {
          target: "idle",
        },
      },
      states: {
        RunningBatchTest: {
          on: {
            "user.pauseTest": {
              target: "#testRunnerActor.TestPaused",
            },
            "test.messageReceived": [
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
                      productAccuracy: getProductAccuracy(
                        (event as any).data.outputTokenCount,
                        context.testCases[context.currentTestIndex]
                          .expectedProducts,
                      ),
                      featureAccuracy: getFeatureAccuracy(
                        (event as any).data.outputTokenCount,
                        context.testCases[context.currentTestIndex]
                          .expectedProducts,
                      ),
                    } as TestResult,
                  ],
                  currentTestIndex: ({ context }) =>
                    context.currentTestIndex + 1,
                }),
                guard: {
                  type: "testIsComplete",
                },
              },
              {
                target: "RunningBatchTest",
              },
            ],
          },
          entry: [
            sendParent(({ context }) => ({
              type: "testRunner.sendMessage",
              data: {
                type: "testRunner.sendMessage",
                sessionId: context.testCases[context.currentTestIndex].id,
                messageId: context.testCases[context.currentTestIndex].id,
                message: context.testCases[context.currentTestIndex].input,
                architectureChoice: "architectureChoice",
                historyManagementChoice: "historyManagementChoice",
              } as RequestData,
            })),
            assign({
              currentTestIndex: ({ context }) => context.currentTestIndex + 1,
            }),
          ],
        },
        EvaluatingFullTestResult: {
          invoke: {
            id: "fullTestEvaluator",
            input: ({ context }) => ({
              testCases: context.testCases,
              testResults: context.testResults,
            }),
            onDone: {
              target: "#testRunnerActor.TestCompleted",
              actions: assign({ fullTestResult: ({ event }) => event.output }),
            },
            src: "fullTestEvaluator",
          },
        },
      },
    },
    TestPaused: {
      on: {
        "user.continueTest": {
          target: "#testRunnerActor.RunningTest.RunningBatchTest",
        },
      },
    },
    TestCompleted: {
      type: "final",
    },
  },
});
