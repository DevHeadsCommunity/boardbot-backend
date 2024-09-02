import { useToast } from "@/hooks/useToast";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { v4 as uuidv4 } from "uuid";
import { useAppContext } from "./useAppContext";

export enum ChatState {
  Idle = "Idle",
  Connecting = "Connecting",
  Typing = "Typing",
  ReceivingResponse = "ReceivingResponse",
}
const stateMap: Record<string, ChatState> = {
  Idle: ChatState.Idle,
  "DisplayingChat.Connecting": ChatState.Connecting,
  "DisplayingChat.Connected.Typing": ChatState.Typing,
  "DisplayingChat.Connected.ReceivingResponse": ChatState.ReceivingResponse,
};

type ChatAction = { type: "user.sendMessage"; messageId: string; message: string };

export const useChatContext = () => {
  const { actorRef } = useAppContext();
  const chatActorRef = actorRef.chat;
  const chatActorState = useSelector(chatActorRef, (state) => state);
  useToast(chatActorRef);

  const chatState = useMemo(() => {
    if (!chatActorState) return ChatState.Idle;
    const currentState = chatActorState.value as string;
    return stateMap[currentState] || ChatState.Idle;
  }, [chatActorState]);

  const chatDispatch = useCallback(
    (action: ChatAction) => {
      chatActorRef?.send(action);
    },
    [chatActorRef]
  );

  console.log("chatState++", chatState);

  return {
    state: {
      chatState,
    },
    data: {
      chatHistory: useSelector(chatActorRef, (state) => state.context.chatHistory || []),
    },
    actions: {
      sendMessage: (message: string) => chatDispatch({ type: "user.sendMessage", messageId: uuidv4(), message }),
    },
  };
};
