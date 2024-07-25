import { ActorRefFrom, assign, emit, fromPromise, sendTo, setup } from "xstate";
import { chatMachine } from "./chatMachine";
import { productMachine } from "./productMachine";
import { testMachine } from "./testMachine";

export const MODEL_VALUES = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] as const;
export type Model = (typeof MODEL_VALUES)[number];
export const ARCHITECTURE_VALUES = ["semantic-router-v1", "agentic-v1", "agentic-v2"] as const;
export type Architecture = (typeof ARCHITECTURE_VALUES)[number];
export const HISTORY_MANAGEMENT_VALUES = ["keep-all", "keep-none", "keep-last-5"] as const;
export type HistoryManagement = (typeof HISTORY_MANAGEMENT_VALUES)[number];

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
      | { type: "user.selectTest" }
      | { type: "user.selectChat" }
      | { type: "user.selectManageProducts" }
      | { type: "user.importState" }
      | { type: "user.exportState" }
      | { type: "user.updateSetting" }
      | { type: "user.submitImportStateForm"; data: { importKey: string } }
      | { type: "user.submitExportStateForm"; data: { exportKey: string } }
      | { type: "user.submitResetSettings" }
      | { type: "user.submitUpdateSettingForm"; data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement } }
      | { type: "user.cancelImportState" }
      | { type: "user.cancelExportState" }
      | { type: "user.cancelUpdateSetting" },
  },
  actors: {
    importState: fromPromise(async ({ input }: { input: { importKey: string } }) => {
      try {
        const data = localStorage.getItem(input.importKey);
        if (!data) {
          throw new Error("No saved state found with the given key");
        }
        return JSON.parse(data);
      } catch (error) {
        throw new Error(`Failed to import state: ${error}`);
      }
    }),
    exportState: fromPromise(async ({ input }: { input: { exportKey: string; state: any } }) => {
      try {
        localStorage.setItem(input.exportKey, JSON.stringify(input.state));
        return { success: true };
      } catch (error) {
        throw new Error(`Failed to export state: ${error}`);
      }
    }),
  },
}).createMachine({
  context: ({ spawn }) => ({
    chatRef: spawn(chatMachine),
    testRef: spawn(testMachine, {
      input: {
        model: "gpt-4o",
        architecture: "semantic-router-v1",
        historyManagement: "keep-all",
      },
    }),
    prodRef: spawn(productMachine),
    model: "gpt-4o",
    architecture: "semantic-router-v1",
    historyManagement: "keep-all",
  }),
  id: "appActor",
  initial: "Open",
  states: {
    Open: {
      initial: "Testing",
      on: {
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
          entry: sendTo(({ context }) => context.chatRef!, {
            type: "app.startChat",
          } as any),
          exit: sendTo(({ context }) => context.chatRef!, {
            type: "app.stopChat",
          } as any),
        },
        Chatting: {
          entry: sendTo(({ context }) => context.prodRef!, {
            type: "app.startManagingProducts",
          } as any),
          exit: sendTo(({ context }) => context.prodRef!, {
            type: "app.stopManagingProducts",
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
              return { importKey: event.data.importKey };
            },
            onDone: {
              target: "#appActor.Open.History",
              actions: [
                assign(({ context, event }) => ({
                  ...event.output,
                  chatRef: context.chatRef,
                  testRef: context.testRef,
                  prodRef: context.prodRef,
                })),
                sendTo(
                  ({ context }) => context.chatRef,
                  ({ event }) => {
                    return {
                      type: "test.restoreState",
                      state: (event as any).output.chatState,
                    };
                  }
                ) as any,
                sendTo(
                  ({ context }) => context.testRef,
                  ({ event }) => {
                    return {
                      type: "test.restoreState",
                      state: (event as any).output.testState,
                    };
                  }
                ) as any,
                sendTo(
                  ({ context }) => context.prodRef,
                  ({ event }) => {
                    return {
                      type: "test.restoreState",
                      state: (event as any).output.prodState,
                    };
                  }
                ) as any,
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
              target: "DisplayingImportStateForm",
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
                exportKey: event.data.exportKey,
                state: {
                  model: context.model,
                  architecture: context.architecture,
                  historyManagement: context.historyManagement,
                  chatState: context.chatRef.getSnapshot(),
                  testState: context.testRef.getSnapshot(),
                  prodState: context.prodRef.getSnapshot(),
                },
              };
            },
            onDone: {
              target: "#appActor.Open.History",
              actions: [
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
              target: "DisplayingExportStateForm",
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
              actions: assign({
                model: ({ event }) => event.data.model,
                architecture: ({ event }) => event.data.architecture,
                historyManagement: ({ event }) => event.data.historyManagement,
              }),
            },
            "user.submitResetSettings": {
              target: "#appActor.Open.History",
              actions: assign({
                model: "gpt-4o",
                architecture: "semantic-router-v1",
                historyManagement: "keep-all",
              }),
            },
          },
        },
      },
    },
  },
});
