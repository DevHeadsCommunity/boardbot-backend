import { ActorRefFrom, assign, emit, fromPromise, sendTo, setup } from "xstate";
import { chatMachine, deserializeChatState, serializeChatState } from "./chatMachine";
import { deserializeProductState, productMachine, serializeProductState } from "./productMachine";
import { deserializeTestState, serializeTestState, testMachine } from "./testMachine";

export const MODEL_VALUES = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] as const;
export type Model = (typeof MODEL_VALUES)[number];
export const ARCHITECTURE_VALUES = ["semantic-router", "llm-router", "hybrid-router", "dynamic-agent"] as const;
export type Architecture = (typeof ARCHITECTURE_VALUES)[number];
export const HISTORY_MANAGEMENT_VALUES = ["keep-none", "keep-last-5", "keep-all"] as const;
export type HistoryManagement = (typeof HISTORY_MANAGEMENT_VALUES)[number];

const serializeAppState = (context: any) => ({
  version: "1.0",
  appState: {
    model: context.model,
    architecture: context.architecture,
    historyManagement: context.historyManagement,
  },
  chatState: serializeChatState(context.chatRef),
  testState: serializeTestState(context.testRef),
  productState: serializeProductState(context.prodRef),
});

const deserializeAppState = (savedState: any, spawn: any) => {
  if (savedState.version !== "1.0") {
    throw new Error("Unsupported state version");
  }
  return {
    ...savedState.appState,
    chatRef: spawn(chatMachine, { input: deserializeChatState(savedState.chatState) }),
    testRef: spawn(testMachine, { input: deserializeTestState(savedState.testState, spawn) }),
    prodRef: spawn(productMachine, { input: deserializeProductState(savedState.productState) }),
  };
};

export const saveToLocalStorage = (key: string, value: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error("Error saving to localStorage:", error);
  }
};

export const loadFromLocalStorage = (key: string) => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (error) {
    console.error("Error loading from localStorage:", error);
    return null;
  }
};

export const exportStateToFile = (state: any, filename: string) => {
  const blob = new Blob([JSON.stringify(state)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
};

export const importStateFromFile = (file: File): Promise<any> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const state = JSON.parse(event.target?.result as string);
        resolve(state);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = (error) => reject(error);
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
      | { type: "user.submitImportStateForm"; data: { file: File } }
      | { type: "user.submitExportStateForm"; data: { fileName: string } }
      | { type: "user.submitResetSettings" }
      | { type: "user.submitUpdateSettingForm"; data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement } }
      | { type: "user.cancelImportState" }
      | { type: "user.cancelExportState" }
      | { type: "user.cancelUpdateSetting" },
  },
  actors: {
    importState: fromPromise(async ({ input }: { input: { file: File } }) => {
      try {
        const importedState = await importStateFromFile(input.file);
        return importedState;
      } catch (error) {
        throw new Error(`Failed to import state: ${error}`);
      }
    }),
    exportState: fromPromise(async ({ input }: { input: { fileName: string; state: any } }) => {
      try {
        await exportStateToFile(input.state, input.fileName);
        return true;
      } catch (error) {
        throw new Error(`Failed to export state: ${error}`);
      }
    }),
  },
}).createMachine({
  context: ({ spawn }) => {
    const savedState = loadFromLocalStorage("appState");
    return savedState
      ? deserializeAppState(savedState, spawn)
      : {
          chatRef: spawn(chatMachine, {
            input: {
              model: "gpt-4o",
              architecture: "llm-router",
              historyManagement: "keep-last-5",
            },
          }),
          testRef: spawn(testMachine, {
            input: {
              model: "gpt-4o",
              architecture: "llm-router",
              historyManagement: "keep-last-5",
            },
          }),
          prodRef: spawn(productMachine, {
            input: {
              model: "gpt-4o",
              architecture: "llm-router",
              historyManagement: "keep-last-5",
            },
          }),
          model: "gpt-4o",
          architecture: "llm-router",
          historyManagement: "keep-last-5",
        };
  },
  id: "appActor",
  initial: "Open",
  states: {
    Open: {
      initial: "Chatting",
      on: {
        "sys.saveState": {
          actions: ({ context }) => {
            const serializedState = serializeAppState(context);
            saveToLocalStorage("appState", serializedState);
          },
        },
        "user.selectTest": {
          target: "#appActor.Open.Testing",
        },
        "user.selectManageProducts": {
          target: "#appActor.Open.ManagingProducts",
        },
        "user.selectChat": {
          target: "#appActor.Open.Chatting",
        },
        "user.importState": {
          target: "ImportingState",
        },
        "user.exportState": {
          target: "ExportingState",
        },
        "user.updateSetting": {
          target: "UpdatingSettings",
        },
      },
      states: {
        Testing: {
          entry: sendTo(({ context }) => context.testRef!, {
            type: "app.startTest",
          } as any),
          exit: sendTo(({ context }) => context.testRef!, {
            type: "app.stopTest",
          } as any),
        },
        ManagingProducts: {
          entry: sendTo(({ context }) => context.prodRef!, {
            type: "app.startManagingProducts",
          } as any),
          exit: sendTo(({ context }) => context.prodRef!, {
            type: "app.stopManagingProducts",
          } as any),
        },
        Chatting: {
          entry: sendTo(({ context }) => context.chatRef!, {
            type: "app.startChat",
          } as any),
          exit: sendTo(({ context }) => context.chatRef!, {
            type: "app.stopChat",
          } as any),
        },
        History: {
          type: "history",
          history: "deep",
        },
      },
    },
    ImportingState: {
      initial: "DisplayingImportStateForm",
      on: {
        "user.cancelImportState": {
          target: "#appActor.Open.History",
        },
      },
      states: {
        DisplayingImportStateForm: {
          on: {
            "user.submitImportStateForm": {
              target: "ImportingState",
            },
          },
        },
        ImportingState: {
          invoke: {
            id: "importState",
            input: ({ event }) => {
              if (event.type !== "user.submitImportStateForm") {
                throw new Error("Invalid event");
              }
              return { file: event.data.file };
            },
            onDone: {
              target: "#appActor.Open.History",
              actions: [
                assign(({ event, spawn }) => {
                  const importedState = event.output;
                  return deserializeAppState(importedState, spawn);
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
              target: "DisplayingImportStateForm",
              actions: emit({
                type: "notification",
                data: {
                  type: "error",
                  message: "Failed to import state",
                },
              }),
            },
            src: "importState",
          },
        },
      },
    },
    ExportingState: {
      initial: "DisplayingExportStateForm",
      on: {
        "user.cancelExportState": {
          target: "#appActor.Open.History",
        },
      },
      states: {
        DisplayingExportStateForm: {
          on: {
            "user.submitExportStateForm": {
              target: "ExportingState",
            },
          },
        },
        ExportingState: {
          invoke: {
            id: "exportState",
            input: ({ context, event }) => {
              if (event.type !== "user.submitExportStateForm") {
                throw new Error("Invalid event");
              }
              return {
                fileName: event.data.fileName,
                state: serializeAppState(context),
              };
            },
            onDone: {
              target: "#appActor.Open.History",
              actions: [
                emit({
                  type: "notification",
                  data: {
                    type: "success",
                    message: "State exported successfully",
                  },
                }),
              ],
            },
            onError: {
              target: "DisplayingExportStateForm",
              actions: emit({
                type: "notification",
                data: {
                  type: "error",
                  message: "Failed to export state",
                },
              }),
            },
            src: "exportState",
          },
        },
      },
    },
    UpdatingSettings: {
      initial: "DisplayingUpdateSettingForm",
      on: {
        "user.cancelUpdateSetting": {
          target: "#appActor.Open.History",
        },
      },
      states: {
        DisplayingUpdateSettingForm: {
          on: {
            "user.submitUpdateSettingForm": {
              target: "#appActor.Open.History",
              actions: [
                assign({
                  model: ({ event }) => event.data.model,
                  architecture: ({ event }) => event.data.architecture,
                  historyManagement: ({ event }) => event.data.historyManagement,
                }),
                sendTo(
                  ({ context }) => context.chatRef!,
                  ({ context }) => ({
                    type: "app.updateState",
                    data: {
                      model: context.model,
                      architecture: context.architecture,
                      historyManagement: context.historyManagement,
                    },
                  })
                ),
                sendTo(
                  ({ context }) => context.testRef!,
                  ({ context }) => ({
                    type: "app.updateState",
                    data: {
                      model: context.model,
                      architecture: context.architecture,
                      historyManagement: context.historyManagement,
                    },
                  })
                ),
              ],
            },
            "user.submitResetSettings": {
              target: "#appActor.Open.History",
              actions: [
                assign({
                  model: "gpt-4o",
                  architecture: "llm-router",
                  historyManagement: "keep-last-5",
                }),
                sendTo(({ context }) => context.chatRef!, {
                  type: "app.updateState",
                  data: {
                    model: "gpt-4o",
                    architecture: "llm-router",
                    historyManagement: "keep-last-5",
                  },
                }),
                sendTo(({ context }) => context.testRef!, {
                  type: "app.updateState",
                  data: {
                    model: "gpt-4o",
                    architecture: "llm-router",
                    historyManagement: "keep-last-5",
                  },
                }),
              ],
            },
          },
        },
      },
    },
  },
});
