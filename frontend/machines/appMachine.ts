import { ActorRefFrom, assign, createMachine, sendTo, setup } from "xstate";
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
      chatRef: ActorRefFrom<typeof chatMachine> | undefined;
      testRef: ActorRefFrom<typeof testMachine> | undefined;
      prodRef: ActorRefFrom<typeof productMachine> | undefined;
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
      | { type: "user.submitImportStateForm" }
      | { type: "user.submitExportStateForm" }
      | { type: "user.submitResetSettings" }
      | { type: "user.submitUpdateSettingForm"; data: { model: Model; architecture: Architecture; historyManagement: HistoryManagement } }
      | { type: "user.cancelImportState" }
      | { type: "user.cancelExportState" }
      | { type: "user.cancelUpdateSetting" },
  },
  actors: {
    importState: createMachine({
      /* ... */
    }),
    exportState: createMachine({
      /* ... */
    }),
  },
}).createMachine({
  context: {
    chatRef: undefined,
    testRef: undefined,
    prodRef: undefined,
    model: "gpt-4o",
    architecture: "semantic-router-v1",
    historyManagement: "keep-all",
  },
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
      entry: assign({
        chatRef: ({ spawn }) => spawn(chatMachine) as any,
        testRef: ({ context, spawn }) =>
          spawn(testMachine, { input: { model: context.model, architecture: context.architecture, historyManagement: context.historyManagement } }) as any,
        prodRef: ({ spawn }) => spawn(productMachine) as any,
      }),
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
          history: "shallow",
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
            input: {},
            onDone: {
              target: "#appActor.Open.History",
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
            input: {},
            onDone: {
              target: "#appActor.Open.History",
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
