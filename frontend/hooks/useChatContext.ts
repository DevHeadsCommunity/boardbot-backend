import { useAppContext } from "@/context/appContext";
import { useToast } from "@/hooks/useToast";
import { useSelector } from "@xstate/react";
import { useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

export enum ChatState {
  Idle = "Idle",
  Connecting = "DisplayingChat.Connecting",
  Typing = "DisplayingChat.Connected.Typing",
  ReceivingResponse = "DisplayingChat.Connected.ReceivingResponse",
}

export const useChatContext = () => {
  const { actorRef } = useAppContext();
  const chatActorRef = actorRef.chat;
  useToast(chatActorRef);

  const chatState = useSelector(chatActorRef, (state) => {
    for (const key in ChatState) {
      if (state.matches(ChatState[key as keyof typeof ChatState] as any)) {
        return ChatState[key as keyof typeof ChatState];
      }
    }
    throw new Error(`Invalid chat state: ${state.value}`);
  });
  console.log("chatState++", chatState);

  const handleSendMessage = useCallback(
    (message: string) => {
      chatActorRef?.send({
        type: "user.sendMessage",
        data: {
          messageId: uuidv4(),
          message,
        },
      });
    },
    [chatActorRef]
  );

  return {
    state: {
      chatState,
    },
    data: {
      chatHistory: useSelector(chatActorRef, (state) => state.context.chatHistory || []),
    },
    actions: {
      handleSendMessage,
    },
  };
};
