import { ChatMessage, RequestData, ResponseData } from "@/types";
import { v4 as uuidv4 } from "uuid";
import { ActorRefFrom, assign, sendTo, setup } from "xstate";
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
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
      restoredState?: any;
    },
    events: {} as
      | { type: "app.startChat" }
      | { type: "app.stopChat" }
      | { type: "webSocket.connected" }
      | { type: "webSocket.messageReceived"; data: ResponseData }
      | { type: "user.sendMessage"; data: { messageId: string; message: string } },
  },
}).createMachine({
  context: ({ input }) => ({
    sessionId: input.restoredState?.sessionId || "",
    webSocketRef: undefined,
    chatHistory: input.restoredState?.chatHistory || [],
    model: input.model,
    architecture: input.architecture,
    historyManagement: input.historyManagement,
  }),
  id: "chatActor",
  initial: "idle",
  // initial: ({input}) => (input.restoredState ? "DisplayingChat" : "idle"),
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

export const getChatMachineState = (chatRef: ActorRefFrom<typeof chatMachine>) => {
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
