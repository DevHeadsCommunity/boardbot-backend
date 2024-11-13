import {
  Architecture,
  ArchitectureSchema,
  ConsistencyTestResult,
  ConsistencyTestResultSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
  Product,
  RequestDataSchema,
  ResponseMessage,
  responseMessageFromJson,
  ResponseMessageSchema,
  TestCase,
  TestCaseSchema,
} from "@/types";
import { assign, sendTo, setup } from "xstate";
import { z } from "zod";
import { webSocketMachine } from "./webSocketMachine";

// Helper functions
function calculateProductConsistency(mainProducts: Product[], variationProductsList: Product[][]): number {
  if (mainProducts.length === 0) {
    const emptyVariations = variationProductsList.filter((products) => products.length === 0);
    return emptyVariations.length / Math.max(variationProductsList.length, 1);
  }

  const mainProductSet = new Set(mainProducts.map((p) => p.name.toLowerCase()));
  const consistencyScores = variationProductsList.map((variationProducts) => {
    const commonProducts = variationProducts.filter((p) => mainProductSet.has(p.name.toLowerCase()));
    return commonProducts.length / Math.max(mainProductSet.size, variationProducts.length, 1);
  });
  return consistencyScores.length > 0 ? consistencyScores.reduce((sum, score) => sum + score, 0) / consistencyScores.length : 0;
}

function calculateOrderConsistency(mainProducts: Product[], variationProductsList: Product[][]): number {
  if (mainProducts.length === 0) {
    const emptyVariations = variationProductsList.filter((products) => products.length === 0);
    return emptyVariations.length / Math.max(variationProductsList.length, 1);
  }

  if (variationProductsList.length === 0) {
    return 0;
  }

  const mainProductOrder = mainProducts.map((p) => p.name.toLowerCase());
  const orderScores = variationProductsList.map((variationProducts) => {
    const variationOrder = variationProducts.map((p) => p.name.toLowerCase());
    return longestCommonSubsequence(mainProductOrder, variationOrder) / Math.max(mainProductOrder.length, variationOrder.length, 1);
  });
  return orderScores.length > 0 ? orderScores.reduce((sum, score) => sum + score, 0) / orderScores.length : 0;
}

function longestCommonSubsequence(arr1: string[], arr2: string[]): number {
  const m = arr1.length;
  const n = arr2.length;
  const dp: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (arr1[i - 1] === arr2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  return dp[m][n];
}

// Zod schema for the context
const ConsistencyTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(ConsistencyTestResultSchema).default([]),
  currentTestIndex: z.number(),
  batchSize: z.number(),
  testTimeout: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
  pendingResponses: z.number(),
  currentResponses: z.array(ResponseMessageSchema).default([]),
});

type ConsistencyTestRunnerContext = z.infer<typeof ConsistencyTestRunnerContextSchema>;

export const consistencyTestRunnerMachine = setup({
  types: {
    context: {} as ConsistencyTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: ConsistencyTestResult[];
      currentTestIndex?: number;
      batchSize?: number;
      testTimeout?: number;
      progress?: number;
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
      pendingResponses?: number;
      currentResponses?: ResponseMessage[];
    },
    events: {} as
      | { type: "user.startTest" }
      | { type: "webSocket.connected" }
      | { type: "user.pauseTest" }
      | { type: "webSocket.messageReceived"; data: ResponseMessage }
      | { type: "user.continueTest" }
      | { type: "user.stopTest" }
      | { type: "webSocket.disconnected" }
      | { type: "internal.sendMessage"; message: { type: string; data: unknown } },
  },
  actions: {
    sendTestCaseMessages: ({ context, self }) => {
      const currentTestCase = context.testCases[context.currentTestIndex];
      const messages = [currentTestCase.prompt, ...currentTestCase.variations!].map((message, index) => ({
        type: "parentActor.sendMessage",
        data: RequestDataSchema.parse({
          type: "textMessage",
          sessionId: context.sessionId,
          messageId: `${currentTestCase.messageId}_${index}`,
          message: message,
          timestamp: new Date().toISOString(),
          model: context.model,
          architectureChoice: context.architecture,
          historyManagementChoice: context.historyManagement,
        }),
      }));

      messages.forEach((message) => {
        self.send({ type: "internal.sendMessage", message });
      });
    },
    sendMessage: sendTo(
      ({ context }) => context.webSocketRef!,
      ({ event }) => {
        if (event.type !== "internal.sendMessage") throw new Error("Invalid event type");
        return {
          type: event.message.type,
          data: event.message.data,
        };
      }
    ),
    setPendingResponses: assign({
      pendingResponses: ({ context }) => context.testCases[context.currentTestIndex].variations!.length,
      currentResponses: [],
    }),
    processResponse: assign({
      pendingResponses: ({ context }) => context.pendingResponses - 1,
      currentResponses: ({ context, event }) => [...context.currentResponses, responseMessageFromJson(event.data)],
    }),
    updateTestResults: assign({
      testResults: ({ context }) => {
        if (context.currentResponses.length === 0) {
          console.warn("No responses to evaluate");
          return context.testResults;
        }
        const mainPromptResponse = context.currentResponses[0];
        const variationResponses = context.currentResponses.slice(1);

        const productConsistency = calculateProductConsistency(
          mainPromptResponse.message.products || [],
          variationResponses.map((r) => r.message.products || [])
        );

        const orderConsistency = calculateOrderConsistency(
          mainPromptResponse.message.products || [],
          variationResponses.map((r) => r.message.products || [])
        );

        const newTestResult: ConsistencyTestResult = {
          mainPromptResponse,
          variationResponses,
          productConsistency,
          orderConsistency,
        };

        return [...context.testResults, newTestResult];
      },
      currentResponses: [],
    }),
    increaseCurrentTestIndex: assign({
      currentTestIndex: ({ context }) => context.currentTestIndex + 1,
    }),
    increaseProgress: assign({
      progress: ({ context }) => ((context.currentTestIndex + 1) / context.testCases.length) * 100,
    }),
  },
  guards: {
    allResponsesReceived: ({ context }) => context.pendingResponses === 0,
    testIsComplete: ({ context }) => context.currentTestIndex >= context.testCases.length,
  },
}).createMachine({
  context: ({ input }) => {
    const parsedContext = ConsistencyTestRunnerContextSchema.parse({
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
      pendingResponses: input.pendingResponses || 0,
      currentResponses: input.currentResponses || [],
    });

    return parsedContext;
  },
  id: "consistencyTestRunnerActor",
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
          entry: ["sendTestCaseMessages", "setPendingResponses"],
          on: {
            "internal.sendMessage": {
              actions: ["sendMessage"],
            },
            "webSocket.messageReceived": [
              {
                actions: ["processResponse"],
                guard: "allResponsesReceived",
                target: "evaluatingResults",
              },
              {
                actions: ["processResponse"],
              },
            ],
          },
        },
        evaluatingResults: {
          entry: ["updateTestResults", "increaseProgress", "increaseCurrentTestIndex"],
          always: [{ target: "#consistencyTestRunnerActor.disconnecting", guard: "testIsComplete" }, { target: "sendingMessage" }],
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
