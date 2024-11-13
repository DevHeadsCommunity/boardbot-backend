import { deepEqual } from "@/lib/utils/comparison";
import {
  Architecture,
  ArchitectureSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
  RequestDataSchema,
  ResponseMessage,
  RobustnessTestResult,
  RobustnessTestResultSchema,
  TestCase,
  TestCaseSchema,
} from "@/types";
import { assign, sendTo, setup } from "xstate";
import { z } from "zod";
import { webSocketMachine } from "./webSocketMachine";

// Helper function to calculate noise filtering score
function calculateNoiseFilteringScore(extractedFilters: Record<string, any>, expectedFilters: Record<string, any>): number {
  if (!expectedFilters || Object.keys(expectedFilters).length === 0) {
    return 1;
  }

  const expectedKeys = Object.keys(expectedFilters);
  const extractedKeys = Object.keys(extractedFilters || {});

  // Calculate precision (correct filters / total extracted)
  const precision =
    extractedKeys.reduce((score, key) => {
      if (expectedKeys.includes(key) && deepEqual(extractedFilters[key], expectedFilters[key])) {
        return score + 1;
      }
      return score;
    }, 0) / Math.max(extractedKeys.length, 1);

  // Calculate recall (correct filters / total expected)
  const recall =
    expectedKeys.reduce((score, key) => {
      if (extractedKeys.includes(key) && deepEqual(extractedFilters[key], expectedFilters[key])) {
        return score + 1;
      }
      return score;
    }, 0) / expectedKeys.length;

  // Return F1 score for balanced measure
  return precision === 0 && recall === 0 ? 0 : (2 * precision * recall) / (precision + recall);
}

// Context schema
const RobustnessTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(RobustnessTestResultSchema).default([]),
  currentTestIndex: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
});

type RobustnessTestRunnerContext = z.infer<typeof RobustnessTestRunnerContextSchema>;

export const robustnessTestRunnerMachine = setup({
  types: {
    context: {} as RobustnessTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: RobustnessTestResult[];
      currentTestIndex?: number;
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
        try {
          const currentTestCase = context.testCases[context.currentTestIndex];
          if (!currentTestCase.expected_filters) {
            console.warn(`Test case ${currentTestCase.messageId} has no expected filters`);
            return [
              ...context.testResults,
              {
                response: event.data,
                filterAccuracy: 1,
                noiseFiltering: 1,
                extractedFilters: {},
              },
            ];
          }

          const testResponse = event.data;
          const extractedFilters = testResponse.message.metadata?.filters || {};
          const filterAccuracy = calculateNoiseFilteringScore(extractedFilters, currentTestCase.expected_filters);

          return [
            ...context.testResults,
            {
              response: testResponse,
              filterAccuracy,
              noiseFiltering: filterAccuracy,
              extractedFilters,
            },
          ];
        } catch (error) {
          console.error("Error updating test results:", error);
          throw error;
        }
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
    RobustnessTestRunnerContextSchema.parse({
      webSocketRef: undefined,
      name: input.name,
      sessionId: input.sessionId,
      testCases: input.testCases,
      testResults: input.testResults || [],
      currentTestIndex: input.currentTestIndex || 0,
      progress: input.progress || 0,
      model: input.model,
      architecture: input.architecture,
      historyManagement: input.historyManagement,
    }),
  id: "robustnessTestRunnerActor",
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
          always: [{ target: "#robustnessTestRunnerActor.disconnecting", guard: "testIsComplete" }, { target: "sendingMessage" }],
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
