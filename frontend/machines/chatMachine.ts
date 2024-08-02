import { ChatMessage, RequestData, ResponseData } from "@/types";
import { v4 as uuidv4 } from "uuid";
import { ActorRefFrom, assign, ContextFrom, sendTo, setup } from "xstate";
import { Architecture, HistoryManagement, Model } from "./appMachine";
import { webSocketMachine } from "./webSocketMachine";

export const chatMachine = setup({
  types: {
    context: {} as {
      sessionId: string;
      webSocketRef: ActorRefFrom<typeof webSocketMachine> | undefined;
      chatHistory: ChatMessage[];
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
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
      | { type: "webSocket.messageReceived"; data: ResponseData }
      | { type: "webSocket.disconnected" }
      | { type: "user.sendMessage"; data: { messageId: string; message: string } },
  },
}).createMachine({
  context: ({ input }) => ({
    sessionId: input?.sessionId || "",
    webSocketRef: undefined,
    chatHistory: input?.chatHistory || [],
    model: input.model,
    architecture: input.architecture,
    historyManagement: input.historyManagement,
  }),
  id: "chatActor",
  initial: "idle",
  // initial: ({input}) => input?.currentState ? input.currentState : "idle", // This is not working, but we need to find a way to restore the state
  on: {
    "app.updateState": {
      actions: assign({
        model: ({ event }) => event.data.model,
        architecture: ({ event }) => event.data.architecture,
        historyManagement: ({ event }) => event.data.historyManagement,
      }),
    },
  },
  states: {
    idle: {
      on: {
        "app.startChat": {
          target: "DisplayingChat",
        },
      },
    },
    DisplayingChat: {
      initial: "Connecting",
      entry: assign({
        sessionId: ({ context }) => context.sessionId || uuidv4(),
        webSocketRef: ({ spawn, context }) => context.webSocketRef || (spawn(webSocketMachine) as any),
      }),
      on: {
        "app.stopChat": {
          target: "idle",
          actions: [
            sendTo(
              ({ context }) => context.webSocketRef!,
              ({ context }) => ({
                type: "parentActor.disconnect",
              })
            ) as any,
          ],
        },
      },
      states: {
        Connecting: {
          entry: sendTo(
            ({ context }) => context.webSocketRef!,
            ({ context }) => ({
              type: "parentActor.connect",
              data: {
                sessionId: context.sessionId,
              },
            })
          ),
          on: {
            "webSocket.connected": {
              target: "Connected",
            },
          },
        },
        Connected: {
          initial: "Typing",
          on: {
            "webSocket.disconnected": {
              target: "Connecting",
            },
          },
          states: {
            Typing: {
              on: {
                "user.sendMessage": {
                  target: "ReceivingResponse",
                  actions: [
                    sendTo(
                      ({ context }) => context.webSocketRef!,
                      ({ context, event }) => ({
                        type: "parentActor.sendMessage",
                        data: {
                          type: "textMessage",
                          sessionId: context.sessionId,
                          messageId: (event as any).data.messageId,
                          message: (event as any).data.message,
                          isComplete: true,
                          timestamp: new Date().toISOString(),
                          model: context.model,
                          architectureChoice: context.architecture,
                          historyManagementChoice: context.historyManagement,
                        } as RequestData,
                      })
                    ) as any,
                    assign({
                      chatHistory: ({ context, event }) => [
                        ...context.chatHistory,
                        {
                          id: (event as any).data.messageId,
                          message: (event as any).data.message,
                          isComplete: false,
                          timestamp: new Date(),
                          isUserMessage: true,
                        },
                      ],
                    }) as any,
                  ],
                },
              },
            },
            ReceivingResponse: {
              on: {
                "webSocket.messageReceived": {
                  target: "Typing",
                  actions: [
                    assign({
                      chatHistory: ({ context, event }) => [
                        ...context.chatHistory,
                        {
                          id: (event as any).data.messageId,
                          message: (event as any).data.message,
                          isComplete: true,
                          timestamp: new Date(),
                          isUserMessage: false,
                          inputTokenCount: (event as any).data.inputTokenCount,
                          outputTokenCount: (event as any).data.outputTokenCount,
                          elapsedTime: (event as any).data.elapsedTime,
                          model: (event as any).data.model,
                        },
                      ],
                    }),
                  ],
                },
              },
            },
          },
        },
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

export const deserializeChatState = (savedState: any): ContextFrom<typeof chatMachine> => {
  return {
    ...savedState,
  };
};
