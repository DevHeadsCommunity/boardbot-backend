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
function calculateProductAccuracy(actualProducts: Product[], expectedProducts: Product[] | undefined): number {
  if (!expectedProducts) {
    return 1;
  }
  const expectedProductNames = new Set(expectedProducts.map((p) => p.name.toLowerCase()));
  const matchedProducts = actualProducts.filter((p) => expectedProductNames.has(p.name.toLowerCase()));
  return matchedProducts.length / expectedProducts.length;
}

function isTestPassed(productAccuracy: number): boolean {
  return productAccuracy > 0.4;
}

// Zod schema for the context
const AccuracyTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(AccuracyTestResultSchema).default([]),
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
          historyManagementChoice: "keep-none",
        }),
      })
    ),
    updateTestResults: assign({
      testResults: ({ context, event }) => {
        if (event.type !== "webSocket.messageReceived") throw new Error("Invalid event type");
        const currentTestCase = context.testCases[context.currentTestIndex];
        if (!currentTestCase.products) {
          throw new Error("Test case has no expected products");
        }

        const testResponse = event.data;
        const productAccuracy = calculateProductAccuracy(testResponse.message.products, currentTestCase.products);
        const testResult: AccuracyTestResult = {
          response: testResponse,
          productAccuracy: productAccuracy,
          passed: isTestPassed(productAccuracy),
        };
        return [...context.testResults, testResult];
      },
    }),
    increaseProgress: assign({
      progress: ({ context }) => ((context.currentTestIndex + 1) / context.testCases.length) * 100,
    }),
    increaseCurrentTestIndex: assign({
      currentTestIndex: ({ context }) => context.currentTestIndex + 1,
    }),
  },
  guards: {
    testIsComplete: ({ context }) => context.currentTestIndex >= context.testCases.length - 1,
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
