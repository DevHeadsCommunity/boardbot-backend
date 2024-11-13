import { deepEqual } from "@/lib/utils/comparison";
import {
  Architecture,
  ArchitectureSchema,
  ContextRetentionTestResult,
  ContextRetentionTestResultSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
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

// Updated context accuracy calculation with better metadata handling
function calculateContextAccuracy(filterProgression: Record<string, any>[]): number {
  if (!filterProgression || filterProgression.length < 2) {
    return 1;
  }

  let totalScore = 0;
  const comparisons = filterProgression.length - 1;

  for (let i = 1; i < filterProgression.length; i++) {
    const current = filterProgression[i];
    const previous = filterProgression[i - 1];

    // Remove metadata fields for comparison
    const currentFilters = { ...current };
    const previousFilters = { ...previous };
    delete currentFilters._turn;
    delete currentFilters._intent;
    delete previousFilters._turn;
    delete previousFilters._intent;

    // Calculate retention score for this turn
    const previousKeys = Object.keys(previousFilters);
    if (previousKeys.length === 0) continue;

    let retainedCount = 0;
    for (const key of previousKeys) {
      if (currentFilters[key] && deepEqual(currentFilters[key], previousFilters[key])) {
        retainedCount++;
      }
    }
    totalScore += retainedCount / previousKeys.length;
  }

  return comparisons > 0 ? totalScore / comparisons : 1;
}

// Simplified context schema
const ContextRetentionTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(ContextRetentionTestResultSchema).default([]),
  currentTestIndex: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
  conversation: z.array(ResponseMessageSchema).default([]),
  conversationIndex: z.number().default(0),
});

type ContextRetentionTestRunnerContext = z.infer<typeof ContextRetentionTestRunnerContextSchema>;

export const contextRetentionTestRunnerMachine = setup({
  types: {
    context: {} as ContextRetentionTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: ContextRetentionTestResult[];
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
    initializeTest: ({ context }) => {
      if (context.testRunnerRef) {
        context.testRunnerRef.send({ type: "user.startTest" });
      }
    },
    sendNextConversationTurn: sendTo(
      ({ context }) => context.webSocketRef!,
      ({ context }) => {
        const currentTestCase = context.testCases[context.currentTestIndex];
        const conversationTurn = currentTestCase.conversation![context.conversationIndex];
        return {
          type: "parentActor.sendMessage",
          data: RequestDataSchema.parse({
            type: "textMessage",
            sessionId: context.sessionId,
            messageId: `${currentTestCase.messageId}_${context.conversationIndex}`,
            message: conversationTurn.query,
            timestamp: new Date().toISOString(),
            model: context.model,
            architectureChoice: context.architecture,
            historyManagementChoice: context.historyManagement,
          }),
        };
      }
    ),
    updateConversation: assign({
      conversation: ({ context, event }) => [...context.conversation, responseMessageFromJson(event.data)],
      conversationIndex: ({ context }) => context.conversationIndex + 1,
    }),
    updateTestResults: assign({
      testResults: ({ context }) => {
        const currentTestCase = context.testCases[context.currentTestIndex];

        // Collect filter progression
        const filterProgression = context.conversation.map((response) => {
          const filters = response.message.metadata?.filters || {};
          return {
            ...filters,
            _turn: response.message.metadata?.turn,
            _intent: response.message.metadata?.intent,
          };
        });

        const contextAccuracy = calculateContextAccuracy(filterProgression);

        const testResult: ContextRetentionTestResult = {
          conversation: context.conversation,
          contextAccuracy,
          filterProgression,
        };
        return [...context.testResults, testResult];
      },
      conversation: [], // Reset conversation for next test
      conversationIndex: 0, // Reset index
    }),
    increaseProgress: assign({
      progress: ({ context }) => ((context.currentTestIndex + 1) / context.testCases.length) * 100,
    }),
    increaseCurrentTestIndex: assign({
      currentTestIndex: ({ context }) => context.currentTestIndex + 1,
    }),
  },
  guards: {
    conversationComplete: ({ context }) => {
      const currentTestCase = context.testCases[context.currentTestIndex];
      return context.conversationIndex >= currentTestCase.conversation!.length;
    },
    testIsComplete: ({ context }) => context.currentTestIndex >= context.testCases.length - 1,
  },
}).createMachine({
  id: "contextRetentionTestRunner",
  initial: "idle",
  context: ({ input }) =>
    ContextRetentionTestRunnerContextSchema.parse({
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
      conversation: [],
      conversationIndex: 0,
    }),
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
      initial: "sendingConversationTurn",
      on: {
        "user.stopTest": {
          target: "disconnecting",
        },
        "user.pauseTest": {
          target: "#contextRetentionTestRunner.running.paused",
        },
      },
      states: {
        sendingConversationTurn: {
          entry: "sendNextConversationTurn",
          on: {
            "webSocket.messageReceived": {
              target: "checkingConversation",
              actions: [
                "updateConversation",
                ({ context }) => {
                  console.log("+++ conversation", context.conversation);
                },
              ],
            },
          },
        },
        checkingConversation: {
          always: [
            {
              guard: "conversationComplete",
              target: "evaluatingResult",
            },
            {
              target: "sendingConversationTurn",
            },
          ],
        },
        evaluatingResult: {
          entry: ["updateTestResults", "increaseCurrentTestIndex", "increaseProgress"],
          always: [
            {
              guard: "testIsComplete",
              target: "#contextRetentionTestRunner.disconnecting",
            },
            {
              target: "sendingConversationTurn",
            },
          ],
        },
        paused: {
          on: {
            "user.continueTest": { target: "sendingConversationTurn" },
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
