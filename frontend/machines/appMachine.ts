import { Architecture, HistoryManagement, Model } from "@/types";
import { ActorRefFrom, assign, emit, fromPromise, sendTo, setup } from "xstate";
import { chatMachine, deserializeChatState, serializeChatState } from "./chatMachine";
import { deserializeProductState, productMachine, serializeProductState } from "./productMachine";
import { deserializeTestState, serializeTestState, testMachine } from "./testMachine";

const APP_STATE_VERSION = "1.1";

const serializeAppState = (context: any) => {
  return {
    version: APP_STATE_VERSION,
    appState: {
      model: context.context.model,
      architecture: context.context.architecture,
      historyManagement: context.context.historyManagement,
    },
    chatState: serializeChatState(context.context.chatRef),
    testState: serializeTestState(context.context.testRef),
    productState: serializeProductState(context.context.prodRef),
  };
};

const deserializeAppState = (savedState: any, spawn: any) => {
  if (savedState.version !== APP_STATE_VERSION) {
    throw new Error(`Unsupported state version. Expected ${APP_STATE_VERSION}, got ${savedState.version}`);
  }
  return {
    ...savedState.appState,
    chatRef: spawn(chatMachine, { input: deserializeChatState(savedState.chatState) }),
    testRef: spawn(testMachine, { input: deserializeTestState(savedState.testState, spawn) }),
    prodRef: spawn(productMachine, { input: deserializeProductState(savedState.productState) }),
  };
};

const saveToLocalStorage = (key: string, value: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error("Error saving to localStorage:", error);
    throw error;
  }
};

const loadFromLocalStorage = (key: string) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error("Error loading from localStorage:", error);
    return null;
  }
};

const exportStateToFile = (state: any, filename: string) => {
  const blob = new Blob([JSON.stringify(state)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
};

const importStateFromFile = async (file: File): Promise<any> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const state = JSON.parse(event.target?.result as string);
        resolve(state);
      } catch (error) {
        reject(new Error("Invalid state file format"));
      }
    };
    reader.onerror = () => reject(new Error("Error reading file"));
    reader.readAsText(file);
  });
};

export const appMachine = setup({
  types: {
    context: {} as {
      chatRef: ActorRefFrom<typeof chatMachine>;
      testRef: ActorRefFrom<typeof testMachine>;
      prodRef: ActorRefFrom<typeof productMachine>;
      model: Model;
      architecture: Architecture;
      historyManagement: HistoryManagement;
    },
    events: {} as
      | { type: "sys.saveState" }
      | { type: "user.selectTest" }
      | { type: "user.selectChat" }
      | { type: "user.selectManageProducts" }
      | { type: "user.importState" }
      | { type: "user.exportState" }
      | { type: "user.updateSetting" }
      | { type: "user.submitImportStateForm"; file: File }
      | { type: "user.submitExportStateForm"; fileName: string }
      | { type: "user.submitResetSettings" }
      | { type: "user.submitUpdateSettingForm"; model: Model; architecture: Architecture; historyManagement: HistoryManagement }
      | { type: "user.cancelImportState" }
      | { type: "user.cancelExportState" }
      | { type: "user.cancelUpdateSetting" },
  },
  actors: {
    importState: fromPromise(async ({ input }: { input: { file: File } }) => {
      try {
        return await importStateFromFile(input.file);
      } catch (error) {
        throw new Error(`Failed to import state: ${error}`);
      }
    }),
    exportState: fromPromise(async ({ input }: { input: { fileName: string; state: any } }) => {
      try {
        exportStateToFile(input.state, input.fileName);
        return true;
      } catch (error) {
        throw new Error(`Failed to export state: ${error}`);
      }
    }),
  },
}).createMachine({
  context: ({ spawn }) => {
    const savedState = loadFromLocalStorage("appState");
    if (savedState) {
      try {
        return deserializeAppState(savedState, spawn);
      } catch (error) {
        console.error("Failed to deserialize saved state:", error);
        // Fall back to default state
      }
    }
    return {
      chatRef: spawn(chatMachine, {
        input: {
          model: "gpt-4o",
          architecture: "dynamic-agent",
          historyManagement: "keep-last-5",
        },
      }),
      testRef: spawn(testMachine, {
        input: {
          model: "gpt-4o",
          architecture: "dynamic-agent",
          historyManagement: "keep-last-5",
        },
      }),
      prodRef: spawn(productMachine, {
        input: {
          model: "gpt-4o",
          architecture: "dynamic-agent",
          historyManagement: "keep-last-5",
        },
      }),
      model: "gpt-4o",
      architecture: "dynamic-agent",
      historyManagement: "keep-last-5",
    };
  },
  id: "appActor",
  initial: "open",
  states: {
    open: {
      initial: "chatting",
      on: {
        "sys.saveState": {
          actions: ({ context }) => {
            const serializedState = serializeAppState({ context });
            saveToLocalStorage("appState", serializedState);
          },
        },
        "user.importState": {
          target: "importingState",
        },
        "user.exportState": {
          target: "exportingState",
        },
        "user.updateSetting": {
          target: "updatingSettings",
        },
        "user.selectTest": {
          target: "#appActor.open.testing",
        },
        "user.selectChat": {
          target: "#appActor.open.chatting",
        },
        "user.selectManageProducts": {
          target: "#appActor.open.managingProducts",
        },
      },
      states: {
        chatting: {
          entry: sendTo(({ context }) => context.chatRef!, {
            type: "app.startChat",
          }),
          exit: sendTo(({ context }) => context.chatRef!, {
            type: "app.stopChat",
          }),
        },
        testing: {
          entry: sendTo(({ context }) => context.testRef!, {
            type: "app.startTest",
          }),
          exit: sendTo(({ context }) => context.testRef!, {
            type: "app.stopTest",
          }),
        },
        managingProducts: {
          entry: sendTo(({ context }) => context.prodRef!, {
            type: "app.startManagingProducts",
          }),
          exit: sendTo(({ context }) => context.prodRef!, {
            type: "app.stopManagingProducts",
          }),
        },
        history: {
          type: "history",
          history: "deep",
        },
      },
    },
    importingState: {
      initial: "displayingImportStateForm",
      on: {
        "user.cancelImportState": {
          target: "#appActor.open.history",
        },
      },
      states: {
        displayingImportStateForm: {
          on: {
            "user.submitImportStateForm": {
              target: "importingState",
            },
          },
        },
        importingState: {
          invoke: {
            id: "importState",
            input: ({ event }) => {
              if (event.type !== "user.submitImportStateForm") {
                throw new Error("Invalid event");
              }
              return { file: event.file };
            },
            onDone: {
              target: "#appActor.open.history",
              actions: [
                assign(({ event, spawn }) => {
                  try {
                    return deserializeAppState(event.output, spawn);
                  } catch (error) {
                    throw new Error(`Invalid state file: ${error instanceof Error ? error.message : "Unknown error"}`);
                  }
                }),
                emit({
                  type: "notification",
                  data: {
                    type: "success",
                    message: "State imported successfully",
                  },
                }),
              ],
            },
            onError: {
              target: "displayingImportStateForm",
              actions: emit({
                type: "notification",
                data: {
                  type: "error",
                  message: `Failed to import state`,
                },
              }),
            },
            src: "importState",
          },
        },
      },
    },
    exportingState: {
      initial: "displayingExportStateForm",
      on: {
        "user.cancelExportState": {
          target: "#appActor.open.history",
        },
      },
      states: {
        displayingExportStateForm: {
          on: {
            "user.submitExportStateForm": {
              target: "exportingState",
            },
          },
        },
        exportingState: {
          invoke: {
            id: "exportState",
            input: ({ context, event }) => {
              if (event.type !== "user.submitExportStateForm") {
                throw new Error("Invalid event");
              }
              return {
                fileName: event.fileName,
                state: serializeAppState(context),
              };
            },
            onDone: {
              target: "#appActor.open.history",
              actions: emit({
                type: "notification",
                data: {
                  type: "success",
                  message: "State exported successfully",
                },
              }),
            },
            onError: {
              target: "displayingExportStateForm",
              actions: emit({
                type: "notification",
                data: {
                  type: "error",
                  message: `Failed to export state`,
                },
              }),
            },
            src: "exportState",
          },
        },
      },
    },
    updatingSettings: {
      initial: "displayingUpdateSettingForm",
      on: {
        "user.cancelUpdateSetting": {
          target: "#appActor.open.history",
        },
      },
      states: {
        displayingUpdateSettingForm: {
          on: {
            "user.submitUpdateSettingForm": {
              target: "#appActor.open.history",
              actions: [
                assign({
                  model: ({ event }) => event.model,
                  architecture: ({ event }) => event.architecture,
                  historyManagement: ({ event }) => event.historyManagement,
                }),
                ({ context }) => {
                  const updateData = {
                    model: context.model,
                    architecture: context.architecture,
                    historyManagement: context.historyManagement,
                  };
                  context.chatRef.send({
                    type: "app.updateState",
                    data: updateData,
                  });
                  context.testRef.send({
                    type: "app.updateState",
                    data: updateData,
                  });
                },
              ],
            },
            "user.submitResetSettings": {
              target: "#appActor.open.history",
              actions: [
                assign({
                  model: "gpt-4o",
                  architecture: "dynamic-agent",
                  historyManagement: "keep-last-5",
                }),
                ({ context }) => {
                  const resetData = {
                    model: "gpt-4o" as Model,
                    architecture: "dynamic-agent" as Architecture,
                    historyManagement: "keep-last-5" as HistoryManagement,
                  };
                  context.chatRef.send({
                    type: "app.updateState",
                    data: resetData,
                  });
                  context.testRef.send({
                    type: "app.updateState",
                    data: resetData,
                  });
                },
              ],
            },
          },
        },
      },
    },
  },
});
