import { ChatMessage, ResponseData } from "@/types";
import { v4 as uuidv4 } from "uuid";
import { assign, emit, sendTo, setup } from "xstate";
import { webSocketMachine } from "./webSocketMachine";

export const chatMachine = setup({
  types: {
    context: {} as {
      webSocketRef: null;
      chatHistory: ChatMessage[]
    },
    events: {} as
      | {
          type: "webSocket.connected";
          data: { sessionId: string; chatHistory: ChatMessage[] };
        }
      | { type: "user.submit"; data: string }
      | { type: "user.typing" }
      | { type: "webSocket.textMessageReceived"; data: ResponseData }
      | { type: "webSocket.disconnected" }
      | { type: "app.startChat" }
      | { type: "app.stopChat" },
  },
  guards: {
    userIsActive: function ({ context, event }) {
      return !context.chatHistory[context.chatHistory.length - 2].id.includes(
        "_hide"
      );
    },
    messageComplete: function ({ context, event }) {
      return context.chatHistory[context.chatHistory.length - 1].isComplete;
    },
  },
}).createMachine({
  context: {
    webSocketRef: null,
    chatHistory: [],
  },
  id: "chatActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "app.startChat": {
          target: "DisplayingChat",
        },
      },
    },
    DisplayingChat: {
      initial: "Setup",
      on: {
        "app.stopChat": {
          target: "idle",
          actions: sendTo(({ context }) => context.webSocketRef!, {
            type: "parentActor.disconnect",
          } as any),
        },
        "webSocket.connected": {
          target: "#chatActor.DisplayingChat.Connected",
          actions: assign({
            chatHistory: ({ event }) => event.data.chatHistory,
          }),
        },
      },
      entry: assign({
        webSocketRef: ({ spawn }) => spawn(webSocketMachine) as any,
      }),
      states: {
        Connected: {
          initial: "ChattingViaText",
          on: {
            "webSocket.disconnected": {
              target: "#chatActor.DisplayingChat",
            },
          },
          states: {
            ChattingViaText: {
              initial: "TextChatOpen",
              states: {
                TextChatOpen: {
                  initial: "initialRender",
                  on: {
                    "user.typing": {
                      target:
                        "#chatActor.DisplayingChat.Connected.ChattingViaText.TextChatOpen.Typing",
                    },
                  },
                  states: {
                    initialRender: {
                      after: {
                        "500000": {
                          target:
                            "#chatActor.DisplayingChat.Connected.ChattingViaText.Responding",
                          actions: sendTo(
                            ({ context }) => context.webSocketRef!,
                            {
                              type: "webSocket.sendMessage",
                              data: {
                                type: "textMessage",
                                message:
                                  "I am new here, can you start the conversation, in a warm and friendly manner. Make your response short and simple. Just tell me a bit about yourself and how you can help me here.",
                                isComplete: true,
                                id: uuidv4() + "_hide",
                              },
                            } as any
                          ) as any,
                        },
                      },
                    },
                    Idle: {},
                    Typing: {
                      on: {
                        "user.submit": {
                          target:
                            "#chatActor.DisplayingChat.Connected.ChattingViaText.Responding",
                          actions: [
                            assign({
                              chatHistory: ({ context, event }) => {
                                const newChat = {
                                  id: uuidv4(),
                                  timestamp: new Date(),
                                  message: event.data,
                                  isUserMessage: true,
                                  isComplete: true,
                                  sentiment: "",
                                };
                                return [...context.chatHistory, newChat];
                              },
                            }),
                            sendTo(
                              ({ context }) => context.webSocketRef!,
                              ({ event }) => {
                                return {
                                  type: "webSocket.sendMessage",
                                  data: {
                                    type: "textMessage",
                                    message: (event as any).data,
                                    isComplete: true,
                                    id: uuidv4(),
                                  },
                                };
                              }
                            ) as any,
                          ],
                        },
                      },
                    },
                    Interactive: {
                      after: {
                        "500000": [
                          {
                            target:
                              "#chatActor.DisplayingChat.Connected.ChattingViaText.Responding",
                            actions: sendTo(
                              ({ context }) => context.webSocketRef!,
                              {
                                type: "webSocket.sendMessage",
                                data: {
                                  type: "textMessage",
                                  message:
                                    "I am a bit lost here, can you let me know how you can help me based on our conversation so far. Make your response short and simple.",
                                  isComplete: true,
                                  id: uuidv4(),
                                },
                              } as any
                            ) as any,
                            guard: {
                              type: "userIsActive",
                            },
                          },
                          {
                            target: "Idle",
                          },
                        ],
                      },
                    },
                  },
                },
                Responding: {
                  initial: "WaitingForFirstChunk",
                  on: {
                    "webSocket.textMessageReceived": {
                      target:
                        "#chatActor.DisplayingChat.Connected.ChattingViaText.Responding.ReceivingResponse",
                      actions: assign({
                        chatHistory: ({
                          context,
                          event,
                        }: {
                          context: any;
                          event: {
                            data: ResponseData;
                          };
                        }) => {
                          const { textResponse, isComplete, id } = event.data;
                          const messageIndex = context.chatHistory.findIndex(
                            (msg: { id: string }) => msg.id === id
                          );
                          if (messageIndex !== -1) {
                            const updatedMessage = {
                              ...context.chatHistory[messageIndex],
                              message:
                                context.chatHistory[messageIndex].message +
                                textResponse,
                              isComplete: isComplete,
                            };
                            const updatedChatHistory = context.chatHistory.map(
                              (msg: { id: string }) =>
                                msg.id === id ? updatedMessage : msg
                            );
                            return updatedChatHistory;
                          } else {
                            const newChat = {
                              id: id,
                              timestamp: new Date(),
                              message: textResponse,
                              isUserMessage: false,
                              isComplete: isComplete,
                              sentiment: "",
                            };
                            return [...context.chatHistory, newChat];
                          }
                        },
                      }),
                    },
                  },
                  states: {
                    WaitingForFirstChunk: {
                      after: {
                        "5000": {
                          target:
                            "#chatActor.DisplayingChat.Connected.ChattingViaText.TextChatOpen",
                          actions: emit({
                            type: "notification",
                            data: {
                              type: "error",
                              message: "Server not responding",
                            },
                          }),
                        },
                      },
                    },
                    ReceivingResponse: {
                      always: [
                        {
                          target:
                            "#chatActor.DisplayingChat.Connected.ChattingViaText.TextChatOpen.Interactive",
                          guard: {
                            type: "messageComplete",
                          },
                        },
                        {
                          target: "WaitingForNextChunk",
                        },
                      ],
                    },
                    WaitingForNextChunk: {
                      after: {
                        "5000": {
                          target:
                            "#chatActor.DisplayingChat.Connected.ChattingViaText.TextChatOpen",
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
  },
});
