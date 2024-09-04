import {
  AccuracyTestResult,
  AccuracyTestResultSchema,
  Architecture,
  ArchitectureSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
  Product,
  RequestDataSchema,
  ResponseMessage,
  TestCase,
  TestCaseSchema,
} from "@/types";
import { assign, sendTo, setup } from "xstate";
import { z } from "zod";
import { webSocketMachine } from "./webSocketMachine";

// Helper functions
function calculateProductAccuracy(actualProducts: Product[], expectedProducts: Product[]): number {
  const expectedProductNames = new Set(expectedProducts.map((p) => p.name.toLowerCase()));
  const matchedProducts = actualProducts.filter((p) => expectedProductNames.has(p.name.toLowerCase()));
  return matchedProducts.length / expectedProducts.length;
}

function calculateFeatureAccuracy(actualProducts: Product[], expectedProducts: Product[]): number {
  let totalFeatures = 0;
  let matchedFeatures = 0;

  expectedProducts.forEach((expectedProduct) => {
    const actualProduct = actualProducts.find((p) => p.name.toLowerCase() === expectedProduct.name.toLowerCase());
    if (actualProduct) {
      Object.keys(expectedProduct).forEach((key) => {
        if (key !== "name" && expectedProduct[key as keyof Product]) {
          totalFeatures++;
          if (JSON.stringify(actualProduct[key as keyof Product]) === JSON.stringify(expectedProduct[key as keyof Product])) {
            matchedFeatures++;
          }
        }
      });
    }
  });

  return totalFeatures > 0 ? matchedFeatures / totalFeatures : 0;
}

// Zod schema for the context
const AccuracyTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(AccuracyTestResultSchema),
  currentTestIndex: z.number(),
  batchSize: z.number(),
  testTimeout: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
});

type AccuracyTestRunnerContext = z.infer<typeof AccuracyTestRunnerContextSchema>;

export const accuracyTestRunnerMachine = setup({
  types: {
    context: {} as AccuracyTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: AccuracyTestResult[];
      currentTestIndex?: number;
      batchSize?: number;
      testTimeout?: number;
      progress?: number;
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    events: {} as
      | { type: "user.startTest" }
      | { type: "webSocket.connected" }
      | { type: "user.pauseTest" }
      | { type: "webSocket.messageReceived"; data: ResponseMessage }
      | { type: "user.continueTest" }
      | { type: "user.stopTest" }
      | { type: "webSocket.disconnected" },
  },
  actions: {
    sendNextMessage: sendTo(
      ({ context }) => context.webSocketRef!,
      ({ context }) => ({
        type: "parentActor.sendMessage",
        data: RequestDataSchema.parse({
          type: "textMessage",
          sessionId: context.sessionId,
          messageId: context.testCases[context.currentTestIndex].messageId,
          message: context.testCases[context.currentTestIndex].prompt,
          timestamp: new Date().toISOString(),
          model: context.model,
          architectureChoice: context.architecture,
          historyManagementChoice: context.historyManagement,
        }),
      })
    ),
    updateTestResults: assign({
      testResults: ({ context, event }) => {
        if (event.type !== "webSocket.messageReceived") throw new Error("Invalid event type");
        const currentTestCase = context.testCases[context.currentTestIndex];
        console.log("===:> currentTestCase", currentTestCase);
        if (!currentTestCase.products) {
          throw new Error("Test case has no expected products");
        }

        console.log("===:> event.data", event.data);
        const testResponse = event.data;
        const testResult: AccuracyTestResult = {
          response: testResponse,
          productAccuracy: calculateProductAccuracy(testResponse.message.products, currentTestCase.products),
          featureAccuracy: calculateFeatureAccuracy(testResponse.message.products, currentTestCase.products),
        };
        return [...context.testResults, testResult];
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
    testIsComplete: ({ context }) => context.currentTestIndex >= context.testCases.length,
  },
}).createMachine({
  context: ({ input }) =>
    AccuracyTestRunnerContextSchema.parse({
      webSocketRef: undefined,
      name: input.name,
      sessionId: input.sessionId,
      testCases: input.testCases,
      testResults: input.testResults || [],
      currentTestIndex: input.currentTestIndex || 0,
      batchSize: input.batchSize || 1,
      progress: input.progress || 0,
      testTimeout: input.testTimeout || 10000,
      model: input.model,
      architecture: input.architecture,
      historyManagement: input.historyManagement,
    }),
  id: "accuracyTestRunnerActor",
  initial: "idle",
  states: {
    idle: {
      entry: assign({
        webSocketRef: ({ spawn }) => spawn(webSocketMachine),
      }),
      on: {
        "user.startTest": { target: "connecting" },
      },
    },
    connecting: {
      entry: sendTo(
        ({ context }) => context.webSocketRef!,
        ({ context }) => ({
          type: "parentActor.connect",
          data: { sessionId: context.sessionId },
        })
      ),
      on: {
        "webSocket.connected": { target: "running" },
      },
    },
    running: {
      initial: "sendingMessage",
      on: {
        "user.stopTest": { target: "disconnecting" },
        "user.pauseTest": { target: ".paused" },
      },
      states: {
        sendingMessage: {
          entry: "sendNextMessage",
          on: {
            "webSocket.messageReceived": [
              {
                target: "evaluatingResult",
                actions: ["updateTestResults", "increaseCurrentTestIndex", "increaseProgress"],
              },
            ],
          },
        },
        evaluatingResult: {
          always: [{ target: "#accuracyTestRunnerActor.disconnecting", guard: "testIsComplete" }, { target: "sendingMessage" }],
        },
        paused: {
          on: {
            "user.continueTest": { target: "sendingMessage" },
          },
        },
      },
    },
    disconnecting: {
      entry: sendTo(({ context }) => context.webSocketRef!, { type: "parentActor.disconnect" }),
      on: {
        "webSocket.disconnected": { target: "idle" },
      },
    },
  },
});
