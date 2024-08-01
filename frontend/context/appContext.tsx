"use client";

import { useToast } from "@/hooks/useToast";
import { appMachine, Architecture, HistoryManagement, Model } from "@/machines/appMachine";
import { createBrowserInspector } from "@statelyai/inspect";
import { useSelector } from "@xstate/react";
import { createContext, useCallback, useContext, useMemo } from "react";
import { ActorRefFrom, createActor } from "xstate";

const { inspect } = createBrowserInspector();
const appActor = createActor(appMachine, {
  inspect,
}).start();

const AppContext = createContext<ActorRefFrom<typeof appMachine> | null>(null);

export const AppContextProvider = ({ children }: { children: React.ReactNode }) => {
  return <AppContext.Provider value={appActor}>{children}</AppContext.Provider>;
};

export enum ChatState {
  Testing = "Testing",
  ManagingProducts = "ManagingProducts",
  Chatting = "Chatting",
  ImportingState = "ImportingState",
  ExportingState = "ExportingState",
  UpdatingSettings = "UpdatingSettings",
}

export const useAppContext = () => {
  const appActorRef = useContext(AppContext);
  if (!appActorRef) {
    throw new Error("useAppContext must be used within an AppContextProvider");
  }
  const state = useSelector(appActorRef, (state) => state);
  useToast(appActorRef);

  const chatState: ChatState = useMemo(() => {
    if (state.matches("Open.Testing" as any)) return ChatState.Testing;
    if (state.matches("Open.ManagingProducts" as any)) return ChatState.ManagingProducts;
    if (state.matches("Open.Chatting" as any)) return ChatState.Chatting;
    if (state.matches("ImportingState")) return ChatState.ImportingState;
    if (state.matches("ExportingState")) return ChatState.ExportingState;
    if (state.matches("UpdatingSettings")) return ChatState.UpdatingSettings;
    return ChatState.Chatting;
  }, [state]);

  const handleSelectTest = useCallback(() => {
    appActorRef.send({ type: "user.selectTest" });
  }, [appActorRef]);
  const handleSelectManageProducts = useCallback(() => {
    appActorRef.send({ type: "user.selectManageProducts" });
  }, [appActorRef]);
  const handleSelectChat = useCallback(() => {
    appActorRef.send({ type: "user.selectChat" });
  }, [appActorRef]);
  const handleImportState = useCallback(() => {
    appActorRef.send({ type: "user.importState" });
  }, [appActorRef]);
  const handleExportState = useCallback(() => {
    appActorRef.send({ type: "user.exportState" });
  }, [appActorRef]);
  const handleUpdateSetting = useCallback(() => {
    appActorRef.send({ type: "user.updateSetting" });
  }, [appActorRef]);
  const handleSubmitImportStateForm = useCallback(
    (data: { importKey: string }) => {
      appActorRef.send({ type: "user.submitImportStateForm", data });
    },
    [appActorRef]
  );
  const handleSubmitExportStateForm = useCallback(
    (data: { exportKey: string }) => {
      appActorRef.send({ type: "user.submitExportStateForm", data });
    },
    [appActorRef]
  );
  const handleSubmitUpdateSettingForm = useCallback(
    (data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement }) => {
      appActorRef.send({ type: "user.submitUpdateSettingForm", data });
    },
    [appActorRef]
  );
  const handleSubmitResetSettings = useCallback(() => {
    appActorRef.send({ type: "user.submitResetSettings" });
  }, [appActorRef]);
  const handleCancelImportState = useCallback(() => {
    appActorRef.send({ type: "user.cancelImportState" });
  }, [appActorRef]);
  const handleCancelExportState = useCallback(() => {
    appActorRef.send({ type: "user.cancelExportState" });
  }, [appActorRef]);
  const handleCancelUpdateSetting = useCallback(() => {
    appActorRef.send({ type: "user.cancelUpdateSetting" });
  }, [appActorRef]);

  return {
    actorRef: {
      chat: state.context.chatRef,
      test: state.context.testRef,
      product: state.context.prodRef,
    },
    state: {
      chatState,
    },
    data: {
      model: useSelector(appActorRef, (state) => state.context.model),
      architecture: useSelector(appActorRef, (state) => state.context.architecture),
      historyManagement: useSelector(appActorRef, (state) => state.context.historyManagement),
    },
    actions: {
      select: {
        test: handleSelectTest,
        manageProducts: handleSelectManageProducts,
        chat: handleSelectChat,
      },
      click: {
        importState: handleImportState,
        exportState: handleExportState,
        updateSetting: handleUpdateSetting,
      },
      submit: {
        importState: handleSubmitImportStateForm,
        exportState: handleSubmitExportStateForm,
        updateSetting: handleSubmitUpdateSettingForm,
        resetSettings: handleSubmitResetSettings,
      },
      cancel: {
        importState: handleCancelImportState,
        exportState: handleCancelExportState,
        updateSetting: handleCancelUpdateSetting,
      },
    },
  };
};

export type AppContextData = ReturnType<typeof useAppContext>["data"];
export type AppContextActions = ReturnType<typeof useAppContext>["actions"];
