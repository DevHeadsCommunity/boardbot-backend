"use client";

import { useToast } from "@/hooks/useToast";
import { Architecture, HistoryManagement, Model } from "@/machines/appMachine";
import { useSelector } from "@xstate/react";
import { useCallback, useContext, useEffect } from "react";
import { AppContext } from "../context/appContext";

export enum AppState {
  Testing = "Open.Testing",
  ManagingProducts = "Open.ManagingProducts",
  Chatting = "Open.Chatting",
  DisplayingImportStateForm = "ImportingState.DisplayingImportStateForm",
  ImportingState = "ImportingState.ImportingState",
  DisplayingExportStateForm = "ExportingState.DisplayingExportStateForm",
  ExportingState = "ExportingState.ExportingState",
  DisplayingUpdateSettingForm = "UpdatingSettings.DisplayingUpdateSettingForm",
  UpdatingSettings = "UpdatingSettings.UpdatingSettings",
}

export const useAppContext = () => {
  const appActorRef = useContext(AppContext);
  if (!appActorRef) {
    throw new Error("useAppContext must be used within an AppContextProvider");
  }
  const state = useSelector(appActorRef, (state) => state);
  useToast(appActorRef);

  const appState: AppState = useSelector(appActorRef, (state) => {
    console.log(`state++: ${JSON.stringify(state.value)}`);
    for (const key in AppState) {
      if (state.matches(AppState[key as keyof typeof AppState] as any)) {
        return AppState[key as keyof typeof AppState];
      }
    }
    throw new Error(`Invalid app state: ${state.value}`);
  });

  useEffect(() => {
    const saveInterval = setInterval(() => {
      appActorRef.send({ type: "sys.saveState" });
    }, 30000); // Save every 30 seconds

    return () => clearInterval(saveInterval);
  }, [appActorRef]);

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
    (data: { file: File }) => {
      appActorRef.send({ type: "user.submitImportStateForm", data });
    },
    [appActorRef]
  );
  const handleSubmitExportStateForm = useCallback(
    (data: { fileName: string }) => {
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
      appState,
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
