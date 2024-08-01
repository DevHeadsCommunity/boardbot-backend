import { RequestData, ResponseData } from "@/types";
import { Socket, io } from "socket.io-client";
import { EventObject, assign, emit, fromCallback, fromPromise, sendParent, setup } from "xstate";

// const SOCKET_URL = "http://18.204.9.187:6789";
// const SOCKET_URL = "http://0.0.0.0:6789";
// const SOCKET_URL = "http://0.0.0.0:5678";
const SOCKET_URL = "http://192.168.118.59:5678";

export const webSocketMachine = setup({
  types: {
    context: {} as { socket: Socket | null; sessionId: string | null },
    events: {} as
      | { type: "parentActor.connect"; data: { sessionId: string } }
      | { type: "parentActor.sendMessage"; data: RequestData }
      | { type: "parentActor.disconnect" }
      | { type: "listener.textResponseReceived" }
      | { type: "listener.disconnected" }
      | { type: "closer.connectionClosed" },
  },
  actions: {
    sendMessage: function ({ context, event }, params: RequestData) {
      const message = {
        ...params,
        sessionId: context.sessionId,
      };
      context.socket?.emit("textMessage", message);
    },
  },
  actors: {
    initializeSocket: fromPromise(
      async ({
        input,
      }: {
        input: { sessionId: string };
      }): Promise<{
        socket: Socket;
        data: ResponseData;
      }> => {
        const sessionId = input.sessionId;
        console.log("===:> sessionId", sessionId);
        try {
          const socket = io(SOCKET_URL, {
            reconnectionAttempts: 5,
            reconnectionDelay: 2000,
          });

          return new Promise((resolve, reject) => {
            socket.on("connect", () => socket.emit("connectionInit"));
            socket.on("connectionAck", () => socket.emit("sessionInit", { sessionId }));
            socket.on("sessionInit", (data: ResponseData) => {
              resolve({ socket, data });
            });
            socket.on("connect_error", reject);
          });
        } catch (error) {
          throw error;
        }
      }
    ),
    listener: fromCallback<EventObject, { socket: Socket; sessionId: string }>(({ sendBack, receive, input }) => {
      const socket = input.socket;
      socket.on("textResponse", (data: ResponseData) => sendBack({ type: "listener.textResponseReceived", data }));
      socket.on("disconnect", () => sendBack({ type: "listener.disconnected" }));

      return () => {
        socket.off("connect");
        socket.off("connectionAck");
        socket.off("sessionInit");
        socket.off("textResponse");
        socket.off("connect_error");
      };
    }),
    closer: fromCallback<EventObject, { socket: Socket }>(({ sendBack, receive, input }) => {
      const socket = input.socket;
      socket.close();
      sendBack({ type: "closer.connectionClosed" });
    }),
  },
}).createMachine({
  context: {
    socket: null,
    sessionId: null,
  },
  id: "webSocketActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "parentActor.connect": {
          target: "Initializing",
          actions: assign({
            sessionId: ({ event }) => event.data.sessionId,
          }),
        },
      },
    },
    Initializing: {
      invoke: {
        id: "initializeSocket",
        input: ({ context }) => {
          if (!context.sessionId) {
            throw new Error("No session id provided");
          }
          return { sessionId: context.sessionId };
        },
        onDone: {
          target: "Connected",
          actions: [
            assign({
              socket: ({ event }) => event.output.socket,
            }),
            sendParent(({ event }) => ({
              type: "webSocket.connected",
              data: event.output.data,
            })),
            emit({
              type: "notification",
              data: {
                type: "success",
                message: "Connected to the server",
              },
            }),
          ],
        },
        onError: {
          target: "Initializing",
          actions: emit({
            type: "notification",
            data: {
              type: "error",
              message: "Failed to connect to the server",
            },
          }),
        },
        src: "initializeSocket",
      },
    },
    Connected: {
      on: {
        "listener.textResponseReceived": {
          actions: sendParent(({ event }: any) => ({
            type: "webSocket.messageReceived",
            data: event.data,
          })),
        },
        "parentActor.sendMessage": {
          actions: {
            type: "sendMessage",
            params: ({ event }: any) => event.data,
          },
        },
        "listener.disconnected": {
          target: "Disconnecting",
        },
        "parentActor.disconnect": {
          target: "Disconnecting",
        },
      },
      invoke: {
        id: "listener",
        input: ({ context }) => {
          if (context.socket && context.sessionId) {
            return { socket: context.socket, sessionId: context.sessionId };
          } else {
            throw new Error("Socket is not available");
          }
        },
        src: "listener",
      },
    },
    Disconnecting: {
      on: {
        "closer.connectionClosed": {
          target: "Disconnected",
          actions: sendParent({ type: "webSocket.disconnected" }),
        },
      },
      invoke: {
        id: "closer",
        input: ({ context }) => {
          if (context.socket) {
            return { socket: context.socket };
          } else {
            throw new Error("Socket is not available");
          }
        },
        src: "closer",
      },
    },
    Disconnected: {
      always: {
        target: "idle",
      },
    },
  },
});
