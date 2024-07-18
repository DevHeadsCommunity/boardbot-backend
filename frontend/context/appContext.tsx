"use client";

import { useToast } from "@/hooks/useToast";
import { appMachine } from "@/machines/appMachine";
import { createBrowserInspector } from "@statelyai/inspect";
import { createActorContext } from "@xstate/react";
import { useEffect, useState } from "react";

const { inspect } = createBrowserInspector();

export const AppContext = createActorContext(appMachine, {
  inspect,
});

export const AppContextProvider = ({ children }: { children: React.ReactNode }) => {
  return <AppContext.Provider>{children}</AppContext.Provider>;
};


export const useAppContext = () => {
  const state = AppContext.useSelector((state) => state);
  const chatActorRef = AppContext.useActorRef();
  const testActorRef = AppContext.useActorRef();
  const productActorRef = AppContext.useActorRef();
  useToast(chatActorRef);
  const [chatState, setChatState] = useState<"Testing" | "ManagingProducts" | "Chatting" | "ImportingState" | "ExportingState" | "UpdatingSettings">("Testing");

  useEffect(() => {
    if (state.matches("Open.Testing" as any)) {
      setChatState("Testing");
    } else if (state.matches("Open.ManagingProducts" as any)) {
      setChatState("ManagingProducts");
    } else if (state.matches("Open.Chatting" as any)) {
      setChatState("Chatting");
    } else if (state.matches("ImportingState")) {
      setChatState("ImportingState");
    } else if (state.matches("ExportingState")) {
      setChatState("ExportingState");
    } else if (state.matches("UpdatingSettings")) {
      setChatState("UpdatingSettings");
    }
  }, [state]);

  const handleSelectTest = () => {
    chatActorRef.send({ type: "user.selectTest" });
  };
  const handleSelectManageProducts = () => {
    chatActorRef.send({ type: "user.selectManageProducts" });
  };
  const handleSelectChat = () => {
    chatActorRef.send({ type: "user.selectChat" });
  };
  const handleImportState = () => {
    chatActorRef.send({ type: "user.importState" });
  }
  const handleExportState = () => {
    chatActorRef.send({ type: "user.exportState" });
  }
  const handleUpdateSetting = () => {
    chatActorRef.send({ type: "user.updateSetting" });
  }
  const handleSubmitImportStateForm = () => {
    chatActorRef.send({ type: "user.submitImportStateForm" });
  }
  const handleSubmitExportStateForm = () => {
    chatActorRef.send({ type: "user.submitExportStateForm" });
  }
  const handleSubmitUpdateSettingForm = () => {
    chatActorRef.send({ type: "user.submitUpdateSettingForm" });
  }
  const handleCancelImportState = () => {
    chatActorRef.send({ type: "user.cancelImportState" });
  }
  const handleCancelExportState = () => {
    chatActorRef.send({ type: "user.cancelExportState" });
  }
  const handleCancelUpdateSetting = () => {
    chatActorRef.send({ type: "user.cancelUpdateSetting" });
  }

  return {
    data: {
      chatState,
    },
    actions: {
      handleSelectTest,
      handleSelectManageProducts,
      handleSelectChat,
      handleImportState,
      handleExportState,
      handleUpdateSetting,
      handleSubmitImportStateForm,
      handleSubmitExportStateForm,
      handleSubmitUpdateSettingForm,
      handleCancelImportState,
      handleCancelExportState,
      handleCancelUpdateSetting,
    },
  };
}

export type AppContextData = ReturnType<typeof useAppContext>["data"];
export type AppContextActions = ReturnType<typeof useAppContext>["actions"];
