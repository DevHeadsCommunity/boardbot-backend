import {
  Architecture,
  ArchitectureSchema,
  DefensibilityTestResult,
  DefensibilityTestResultSchema,
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

// Helper function to evaluate appropriate response
function isResponseAppropriate(response: ResponseMessage, expectedMessage: string): boolean {
  return response.message.message.trim() === expectedMessage.trim();
}

// Context schema
const DefensibilityTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(DefensibilityTestResultSchema).default([]),
  currentTestIndex: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
  conversation: z.array(ResponseMessageSchema).default([]),
  conversationIndex: z.number().default(0),
});

type DefensibilityTestRunnerContext = z.infer<typeof DefensibilityTestRunnerContextSchema>;

export const defensibilityTestRunnerMachine = setup({
  types: {
    context: {} as DefensibilityTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: DefensibilityTestResult[];
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
        const lastResponse = context.conversation[context.conversation.length - 1];
        const expectedMessage = currentTestCase.conversation![context.conversationIndex - 1].message!;
        const appropriateResponse = isResponseAppropriate(lastResponse, expectedMessage);

        const testResult: DefensibilityTestResult = {
          conversation: context.conversation,
          boundaryMaintenance: appropriateResponse ? 1 : 0,
          appropriateResponse,
        };
        return [...context.testResults, testResult];
      },
      conversation: [],
      conversationIndex: 0,
      currentTestIndex: ({ context }) => context.currentTestIndex + 1,
      progress: ({ context }) => ((context.currentTestIndex + 1) / context.testCases.length) * 100,
    }),
  },
  guards: {
    conversationComplete: ({ context }) => {
      const currentTestCase = context.testCases[context.currentTestIndex];
      return context.conversationIndex >= currentTestCase.conversation!.length;
    },
    testIsComplete: ({ context }) => {
      return context.currentTestIndex >= context.testCases.length;
    },
  },
}).createMachine({
  context: ({ input }) =>
    DefensibilityTestRunnerContextSchema.parse({
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
  id: "defensibilityTestRunnerActor",
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
      initial: "sendingConversationTurn",
      on: {
        "user.stopTest": { target: "disconnecting" },
        "user.pauseTest": { target: ".paused" },
      },
      states: {
        sendingConversationTurn: {
          entry: "sendNextConversationTurn",
          on: {
            "webSocket.messageReceived": {
              target: "checkingConversation",
              actions: "updateConversation",
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
          entry: "updateTestResults",
          always: [
            {
              guard: "testIsComplete",
              target: "#defensibilityTestRunnerActor.disconnecting",
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
