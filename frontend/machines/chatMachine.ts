import {
  Architecture,
  ArchitectureSchema,
  ChatMessage,
  ChatMessageSchema,
  HistoryManagement,
  HistoryManagementSchema,
  Model,
  ModelSchema,
  RequestDataSchema,
  ResponseMessage,
} from "@/types";
import { v4 as uuidv4 } from "uuid";
import { ActorRefFrom, assign, ContextFrom, sendTo, setup } from "xstate";
import { z } from "zod";
import { webSocketMachine } from "./webSocketMachine";

const ChatContextSchema = z.object({
  sessionId: z.string(),
  webSocketRef: z.any(), // Can't directly validate ActorRef with Zod
  chatHistory: z.array(ChatMessageSchema),
  model: ModelSchema,
  architecture: ArchitectureSchema,
  historyManagement: HistoryManagementSchema,
});

type ChatContext = z.infer<typeof ChatContextSchema>;

export const chatMachine = setup({
  types: {
    context: {} as ChatContext,
    input: {} as {
      sessionId?: string;
      chatHistory?: ChatMessage[];
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    events: {} as
      | { type: "app.startChat" }
      | { type: "app.stopChat" }
      | { type: "app.updateState"; data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement } }
      | { type: "webSocket.connected" }
      | { type: "webSocket.messageReceived"; data: ResponseMessage }
      | { type: "webSocket.disconnected" }
      | { type: "user.sendMessage"; messageId: string; message: string },
  },
}).createMachine({
  context: ({ input, spawn }) =>
    ChatContextSchema.parse({
      sessionId: input?.sessionId || uuidv4(),
      webSocketRef: spawn(webSocketMachine),
      chatHistory: input?.chatHistory || [],
      model: input.model,
      architecture: input.architecture,
      historyManagement: input.historyManagement,
    }),
  id: "chatActor",
  initial: "idle",
  on: {
    "app.updateState": {
      actions: assign(({ context, event }) => ({
        model: event.data.model,
        architecture: event.data.architecture,
        historyManagement: event.data.historyManagement,
      })),
    },
  },
  states: {
    idle: {
      on: {
        "app.startChat": { target: "connecting" },
      },
    },
    connecting: {
      entry: sendTo(
        ({ context }) => context.webSocketRef,
        ({ context }) => ({
          type: "parentActor.connect",
          data: { sessionId: context.sessionId },
        })
      ),
      on: {
        "webSocket.connected": { target: "chatting" },
      },
    },
    chatting: {
      initial: "awaitingUserInput",
      on: {
        "app.stopChat": {
          target: "disconnecting",
        },
        "webSocket.disconnected": {
          target: "connecting",
        },
      },
      states: {
        awaitingUserInput: {
          on: {
            "user.sendMessage": {
              target: "processingMessage",
              actions: [
                sendTo(
                  ({ context }) => context.webSocketRef,
                  ({ context, event }) => ({
                    type: "parentActor.sendMessage",
                    data: RequestDataSchema.parse({
                      type: "textMessage",
                      sessionId: context.sessionId,
                      messageId: event.messageId,
                      message: event.message,
                      isComplete: true,
                      timestamp: new Date().toISOString(),
                      model: context.model,
                      architectureChoice: context.architecture,
                      historyManagementChoice: context.historyManagement,
                    }),
                  })
                ),
                assign({
                  chatHistory: ({ context, event }) => [
                    ...context.chatHistory,
                    ChatMessageSchema.parse({
                      sessionId: context.sessionId,
                      messageId: event.messageId,
                      timestamp: new Date(),
                      isUserMessage: true,
                      isComplete: true,
                      model: context.model,
                      architectureChoice: context.architecture,
                      historyManagementChoice: context.historyManagement,
                      message: event.message,
                    }),
                  ],
                }),
              ],
            },
          },
        },
        processingMessage: {
          on: {
            "webSocket.messageReceived": {
              target: "awaitingUserInput",
              actions: assign({
                chatHistory: ({ context, event }) => [
                  ...context.chatHistory,
                  ChatMessageSchema.parse({
                    sessionId: context.sessionId,
                    messageId: event.data.messageId,
                    timestamp: new Date(),
                    isUserMessage: false,
                    isComplete: true,
                    model: event.data.model,
                    architectureChoice: context.architecture,
                    historyManagementChoice: context.historyManagement,
                    message: event.data.message,
                  }),
                ],
              }),
            },
          },
        },
      },
    },
    disconnecting: {
      entry: sendTo(({ context }) => context.webSocketRef, { type: "parentActor.disconnect" }),
      on: {
        "webSocket.disconnected": { target: "idle" },
      },
    },
  },
});

export const serializeChatState = (chatRef: ActorRefFrom<typeof chatMachine>) => {
  const snapshot = chatRef.getSnapshot();
  return {
    sessionId: snapshot.context.sessionId,
    chatHistory: snapshot.context.chatHistory,
    model: snapshot.context.model,
    architecture: snapshot.context.architecture,
    historyManagement: snapshot.context.historyManagement,
    currentState: snapshot.value,
  };
};

export const deserializeChatState = (savedState: unknown): ContextFrom<typeof chatMachine> => {
  const parsedState = ChatContextSchema.parse(savedState);
  return {
    ...parsedState,
    webSocketRef: undefined, // Will be re-spawned when the machine starts
  };
};
