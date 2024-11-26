import {
  Architecture,
  ArchitectureSchema,
  ConversationalFlowTestResult,
  ConversationalFlowTestResultSchema,
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

// Improved similarity calculation using cosine similarity
function calculateSimilarity(text1: string, text2: string): number {
  const getWordFrequency = (text: string) => {
    const words = text.toLowerCase().split(/\s+/);
    return words.reduce((freq: Record<string, number>, word) => {
      freq[word] = (freq[word] || 0) + 1;
      return freq;
    }, {});
  };

  const freq1 = getWordFrequency(text1);
  const freq2 = getWordFrequency(text2);
  const allWords = new Set([...Object.keys(freq1), ...Object.keys(freq2)]);

  let dotProduct = 0;
  let magnitude1 = 0;
  let magnitude2 = 0;

  for (const word of allWords) {
    const f1 = freq1[word] || 0;
    const f2 = freq2[word] || 0;
    dotProduct += f1 * f2;
    magnitude1 += f1 * f1;
    magnitude2 += f2 * f2;
  }

  const magnitude = Math.sqrt(magnitude1) * Math.sqrt(magnitude2);
  return magnitude === 0 ? 0 : dotProduct / magnitude;
}

// Enhanced flow coherence calculation with weighted scoring
function calculateFlowCoherence(conversation: ResponseMessage[]): number {
  if (conversation.length <= 1) return 1;

  let coherenceScore = 0;
  const weights = conversation.map((_, i) => Math.pow(0.9, conversation.length - i - 1));
  let weightSum = weights.slice(1).reduce((sum, w) => sum + w, 0);

  for (let i = 1; i < conversation.length; i++) {
    const previousResponse = conversation[i - 1].message.message;
    const currentResponse = conversation[i].message.message;
    const similarity = calculateSimilarity(previousResponse, currentResponse);
    coherenceScore += similarity * weights[i];
  }

  return coherenceScore / weightSum;
}

// Improved topic transition accuracy with context windows
function calculateTopicTransitionAccuracy(conversation: ResponseMessage[]): number {
  if (conversation.length <= 2) return 1;

  const CONTEXT_WINDOW = 3;
  let transitionScore = 0;
  let transitions = 0;

  for (let i = CONTEXT_WINDOW; i < conversation.length; i++) {
    const currentWindow = conversation.slice(i - CONTEXT_WINDOW, i + 1);
    const previousContext = currentWindow
      .slice(0, -1)
      .map((msg) => msg.message.message)
      .join(" ");
    const currentMessage = currentWindow[currentWindow.length - 1].message.message;

    const contextSimilarity = calculateSimilarity(previousContext, currentMessage);
    transitionScore += contextSimilarity;
    transitions++;
  }

  return transitions > 0 ? transitionScore / transitions : 1;
}

// Context schema
const ConversationalFlowTestRunnerContextSchema = z.object({
  webSocketRef: z.any().optional(),
  name: z.string(),
  sessionId: z.string(),
  testCases: z.array(TestCaseSchema),
  testResults: z.array(ConversationalFlowTestResultSchema).default([]),
  currentTestIndex: z.number(),
  progress: z.number(),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
  conversation: z.array(ResponseMessageSchema).default([]),
  conversationIndex: z.number().default(0),
});

type ConversationalFlowTestRunnerContext = z.infer<typeof ConversationalFlowTestRunnerContextSchema>;

export const conversationalFlowTestRunnerMachine = setup({
  types: {
    context: {} as ConversationalFlowTestRunnerContext,
    input: {} as {
      name: string;
      sessionId: string;
      testCases: TestCase[];
      testResults?: ConversationalFlowTestResult[];
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
        const flowCoherence = calculateFlowCoherence(context.conversation);
        const topicTransitionAccuracy = calculateTopicTransitionAccuracy(context.conversation);

        const testResult: ConversationalFlowTestResult = {
          conversation: context.conversation,
          flowCoherence,
          topicTransitionAccuracy,
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
    ConversationalFlowTestRunnerContextSchema.parse({
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
  id: "conversationalFlowTestRunnerActor",
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
              target: "#conversationalFlowTestRunnerActor.disconnecting",
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
