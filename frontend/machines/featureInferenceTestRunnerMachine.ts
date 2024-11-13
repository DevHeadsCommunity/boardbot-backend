import { deepEqual } from "@/lib/utils/comparison";
import {
  Architecture,
  ArchitectureSchema,
  FeatureInferenceTestResult,
  FeatureInferenceTestResultSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
  RequestDataSchema,
  ResponseMessage,
  TestCase,
  TestCaseSchema,
} from "@/types";
import { assign, sendTo, setup } from "xstate";
import { z } from "zod";
import { webSocketMachine } from "./webSocketMachine";

// Update the calculateFilterAccuracy function
function calculateFilterAccuracy(extractedFilters: Record<string, any>, expectedFilters: Record<string, any>): number {
  if (!expectedFilters || Object.keys(expectedFilters).length === 0) {
    return 1;
  }

  const expectedKeys = Object.keys(expectedFilters);
  const extractedKeys = Object.keys(extractedFilters || {});
  let matchedFilters = 0;
  let totalFilters = expectedKeys.length;

  // Check for both key presence and value match
  for (const key of expectedKeys) {
    if (extractedKeys.includes(key)) {
      // Handle different value types (string, number, array, object)
      const expectedValue = expectedFilters[key];
      const extractedValue = extractedFilters[key];
      if (deepEqual(expectedValue, extractedValue)) {
        matchedFilters++;
      }
    }
  }

  return totalFilters > 0 ? matchedFilters / totalFilters : 1;
}

// Context schema
const FeatureInferenceTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(FeatureInferenceTestResultSchema).default([]),
  currentTestIndex: z.number(),
  testTimeout: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
});

type FeatureInferenceTestRunnerContext = z.infer<typeof FeatureInferenceTestRunnerContextSchema>;

export const featureInferenceTestRunnerMachine = setup({
  types: {
    context: {} as FeatureInferenceTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: FeatureInferenceTestResult[];
      currentTestIndex?: number;
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
        if (!currentTestCase.expected_filters) {
          console.warn("Test case has no expected filters, treating as success");
          return [
            ...context.testResults,
            {
              response: event.data,
              filterAccuracy: 1,
              extractedFilters: {},
              expectedFilters: {},
            },
          ];
        }

        const testResponse = event.data;
        const extractedFilters = testResponse.message.metadata?.filters || {};
        const filterAccuracy = calculateFilterAccuracy(extractedFilters, currentTestCase.expected_filters);

        const testResult: FeatureInferenceTestResult = {
          response: testResponse,
          filterAccuracy,
          extractedFilters,
          expectedFilters: currentTestCase.expected_filters,
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
    FeatureInferenceTestRunnerContextSchema.parse({
      webSocketRef: undefined,
      name: input.name,
      sessionId: input.sessionId,
      testCases: input.testCases,
      testResults: input.testResults || [],
      currentTestIndex: input.currentTestIndex || 0,
      progress: input.progress || 0,
      testTimeout: input.testTimeout || 10000,
      model: input.model,
      architecture: input.architecture,
      historyManagement: input.historyManagement,
    }),
  id: "featureInferenceTestRunnerActor",
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
          always: [{ target: "#featureInferenceTestRunnerActor.disconnecting", guard: "testIsComplete" }, { target: "sendingMessage" }],
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
