import { RequestData, ResponseData } from "@/types";
import Cookies from "js-cookie";
import { Socket, io } from "socket.io-client";
import { v4 as uuidv4 } from "uuid";
import {
  EventObject,
  assign,
  emit,
  fromCallback,
  fromPromise,
  sendParent,
  setup,
} from "xstate";

// const SOCKET_URL = "http://18.204.9.187:6789";
const SOCKET_URL = "http://0.0.0.0:6789";

export const webSocketMachine = setup({
  types: {
    context: {} as { socket: Socket | null; sessionId: string | null },
    events: {} as
      | { type: "listener.textResponseReceived" }
      | { type: "webSocket.sendMessage" }
      | { type: "listener.disconnected" }
      | { type: "closer.connectionClosed" }
      | { type: "parentActor.disconnect" },
  },
  actions: {
    sendMessage: function ({ context, event }, params: RequestData) {
      const message = {
        ...params,
        sessionId: context.sessionId,
      };
      context.socket?.emit("chat_message", message);
    },
  },
  actors: {
    initializeSocket: fromPromise(
      async (): Promise<{
        socket: Socket;
        sessionId: string;
        data: ResponseData;
      }> => {
        try {
          const sessionId = Cookies.get("sessionId") || uuidv4();
          if (!Cookies.get("sessionId")) {
            Cookies.set("sessionId", sessionId);
          }

          const socket = io(SOCKET_URL, {
            reconnectionAttempts: 5,
            reconnectionDelay: 2000,
          });

          return new Promise((resolve, reject) => {
            socket.on("connect", () =>
              socket.emit("chat_message", { type: "connectionInit" })
            );
            socket.on("connectionAck", () =>
              socket.emit("chat_message", { type: "sessionInit", sessionId })
            );
            socket.on("sessionInit", (data: ResponseData) => {
              resolve({ socket, sessionId, data });
            });
            socket.on("connect_error", reject);
          });
        } catch (error) {
          throw error;
        }
      }
    ),
    listener: fromCallback<EventObject, { socket: Socket; sessionId: string }>(
      ({ sendBack, receive, input }) => {
        const socket = input.socket;
        socket.on("textResponse", (data: ResponseData) =>
          sendBack({ type: "listener.textResponseReceived", data })
        );
        socket.on("audioTranscription", (data: ResponseData) =>
          sendBack({ type: "listener.transcriptionReceived", data })
        );
        socket.on("audioResponse", (data: ResponseData) =>
          sendBack({ type: "listener.audioResponseReceived", data })
        );
        socket.on("scheduleMeeting", (data: ResponseData) =>
          sendBack({ type: "listener.meetingDetailsReceived", data })
        );
        socket.on("disconnect", () =>
          sendBack({ type: "listener.disconnected" })
        );

        return () => {
          socket.off("connect");
          socket.off("connectionAck");
          socket.off("sessionInit");
          socket.off("textResponse");
          socket.off("audioTranscription");
          socket.off("audioResponse");
          socket.off("scheduleMeeting");
          socket.off("connect_error");
        };
      }
    ),
    closer: fromCallback<EventObject, { socket: Socket }>(
      ({ sendBack, receive, input }) => {
        const socket = input.socket;
        socket.close();
        sendBack({ type: "closer.connectionClosed" });
      }
    ),
  },
}).createMachine({
  context: {
    socket: null,
    sessionId: null,
  },
  id: "webSocketActor",
  initial: "Initializing",
  states: {
    Initializing: {
      invoke: {
        id: "initializeSocket",
        input: {},
        onDone: {
          target: "Connected",
          actions: [
            assign({
              socket: ({ event }) => event.output.socket,
              sessionId: ({ event }) => event.output.sessionId,
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
            type: "webSocket.textMessageReceived",
            data: event.data,
          })),
        },
        "webSocket.sendMessage": {
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
    Disconnected: {},
  },
});
