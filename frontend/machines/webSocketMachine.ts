import { RequestData, RequestDataSchema, ResponseMessage, requestDataToJson, responseMessageFromJson } from "@/types";
import { Socket, io } from "socket.io-client";
import { EventObject, assign, emit, fromCallback, fromPromise, sendParent, setup } from "xstate";
import { z } from "zod";

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL;
if (!SOCKET_URL) {
  throw new Error("Missing env variable NEXT_PUBLIC_SOCKET_URL");
}

const MAX_RECONNECTION_ATTEMPTS = 5;
const RECONNECTION_DELAY = 2000;

const WebSocketContextSchema = z.object({
  socket: z.any().nullable(), // Can't directly validate Socket with Zod
  sessionId: z.string().nullable(),
  reconnectionAttempts: z.number(),
});

type WebSocketContext = z.infer<typeof WebSocketContextSchema>;

export const webSocketMachine = setup({
  types: {
    context: {} as WebSocketContext,
    events: {} as
      | { type: "parentActor.connect"; data: { sessionId: string } }
      | { type: "parentActor.sendMessage"; data: RequestData }
      | { type: "parentActor.disconnect" }
      | { type: "socketListener.messageReceived"; data: ResponseMessage }
      | { type: "socketListener.disconnected" },
  },
  actions: {
    sendMessage: ({ context, event }) => {
      if (event.type !== "parentActor.sendMessage") return;
      const message = RequestDataSchema.parse({
        ...event.data,
        sessionId: context.sessionId,
      });

      const snake_case_message = requestDataToJson(message);
      console.log("\n\n:===> Sending message:", snake_case_message, "\n\n");
      context.socket?.emit("text_message", snake_case_message);
    },
  },
  actors: {
    socketConnector: fromPromise(async ({ input }: { input: { sessionId: string } }): Promise<{ socket: Socket; data: ResponseMessage }> => {
      return new Promise((resolve, reject) => {
        const socket = io(SOCKET_URL, {
          reconnectionAttempts: MAX_RECONNECTION_ATTEMPTS,
          reconnectionDelay: RECONNECTION_DELAY,
        });

        socket.on("connect", () => socket.emit("connection_init"));
        socket.on("connection_ack", () => socket.emit("session_init", { session_id: input.sessionId }));
        socket.on("session_init", (data: any) => {
          console.log("Session init data:", data);
          resolve({ socket, data });
        });
        socket.on("connect_error", reject);
      });
    }),
    socketListener: fromCallback<EventObject, { socket: Socket }>(({ sendBack, input }) => {
      const { socket } = input;

      const handleTextResponse = (data: unknown) => {
        try {
          const validatedData = responseMessageFromJson(data);
          console.log("\n\n:===> Received message:", validatedData, "\n\n");
          sendBack({ type: "socketListener.messageReceived", data: validatedData });
        } catch (error) {
          console.error("Invalid response data:", error);
        }
      };

      socket.on("text_response", handleTextResponse);
      socket.on("disconnect", () => sendBack({ type: "socketListener.disconnected" }));

      return () => {
        socket.off("text_response", handleTextResponse);
        socket.off("disconnect");
      };
    }),
  },
  guards: {
    canReconnect: ({ context }) => context.reconnectionAttempts < MAX_RECONNECTION_ATTEMPTS,
  },
}).createMachine({
  context: WebSocketContextSchema.parse({
    socket: null,
    sessionId: null,
    reconnectionAttempts: 0,
  }),
  id: "webSocketActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "parentActor.connect": {
          target: "connecting",
          actions: assign({
            sessionId: ({ event }) => event.data.sessionId,
            reconnectionAttempts: 0,
          }),
        },
      },
    },
    connecting: {
      invoke: {
        src: "socketConnector",
        input: ({ context }) => ({ sessionId: context.sessionId! }),
        onDone: {
          target: "connected",
          actions: [
            assign({ socket: ({ event }) => event.output.socket }),
            sendParent({ type: "webSocket.connected" }),
            emit({
              type: "notification",
              data: { type: "success", message: "Connected to the server" },
            }),
          ],
        },
        onError: {
          target: "reconnecting",
          actions: emit({
            type: "notification",
            data: { type: "error", message: "Failed to connect to the server" },
          }),
        },
      },
    },
    connected: {
      invoke: {
        src: "socketListener",
        input: ({ context }) => ({ socket: context.socket! }),
      },
      on: {
        "parentActor.sendMessage": { actions: "sendMessage" },
        "socketListener.messageReceived": {
          actions: sendParent(({ event }) => ({
            type: "webSocket.messageReceived",
            data: event.data,
          })),
        },
        "socketListener.disconnected": { target: "reconnecting" },
        "parentActor.disconnect": { target: "disconnecting" },
      },
    },
    reconnecting: {
      entry: assign({
        reconnectionAttempts: ({ context }) => context.reconnectionAttempts + 1,
      }),
      always: [
        {
          guard: "canReconnect",
          target: "idle",
          actions: emit({
            type: "notification",
            data: { type: "error", message: "Failed to reconnect after multiple attempts" },
          }),
        },
        { target: "connecting" },
      ],
    },
    disconnecting: {
      entry: [({ context }) => context.socket?.close(), sendParent({ type: "webSocket.disconnected" })],
      always: { target: "idle" },
    },
  },
});
