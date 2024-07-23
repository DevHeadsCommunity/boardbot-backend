"use client";

import { useToast } from "@/hooks/useToast";
import { appMachine, Architecture, HistoryManagement, Model } from "@/machines/appMachine";
import { createBrowserInspector } from "@statelyai/inspect";
import { createActorContext, useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";

const { inspect } = createBrowserInspector();

export const AppContext = createActorContext(appMachine, {
  inspect,
});

export const AppContextProvider = ({ children }: { children: React.ReactNode }) => {
  return <AppContext.Provider>{children}</AppContext.Provider>;
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
  const state = AppContext.useSelector((state) => state);
  const appActorRef = AppContext.useActorRef();
  useToast(appActorRef);

  const chatState = useMemo(() => {
    if (state.matches("Open.Testing" as any)) return ChatState.Testing;
    if (state.matches("Open.ManagingProducts" as any)) return ChatState.ManagingProducts;
    if (state.matches("Open.Chatting" as any)) return ChatState.Chatting;
    if (state.matches("ImportingState")) return ChatState.ImportingState;
    if (state.matches("ExportingState")) return ChatState.ExportingState;
    if (state.matches("UpdatingSettings")) return ChatState.UpdatingSettings;
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
  const handleSubmitImportStateForm = useCallback(() => {
    appActorRef.send({ type: "user.submitImportStateForm" });
  }, [appActorRef]);
  const handleSubmitExportStateForm = useCallback(() => {
    appActorRef.send({ type: "user.submitExportStateForm" });
  }, [appActorRef]);
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
