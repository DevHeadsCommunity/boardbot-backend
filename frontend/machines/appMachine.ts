import { assign, createMachine, sendTo, setup } from "xstate";
import { chatMachine } from "./chatMachine";
import { productMachine } from './productMachine';
import { testMachine } from './testMachine';

export const appMachine = setup({
  types: {
    context: {} as { chatRef: null; testRef: null; prodRef: null },
    events: {} as
      | { type: "user.selectTest" }
      | { type: "user.selectManageProducts" }
      | { type: "user.selectChat" }
      | { type: "user.importState" }
      | { type: "user.exportState" }
      | { type: "user.submitImportStateForm" }
      | { type: "user.cancelImportState" }
      | { type: "user.submitExportStateForm" }
      | { type: "user.cancelExportState" }
      | { type: "user.updateSetting" }
      | { type: "user.cancelUpdateSetting" }
      | { type: "user.submitUpdateSettingForm" },
  },
  actors: {
    importState: createMachine({
      /* ... */
    }),
    exportState: createMachine({
      /* ... */
    }),
    updateSettings: createMachine({
      /* ... */
    }),
  },
}).createMachine({
  context: {
    chatRef: null,
    testRef: null,
    prodRef: null,
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
        testRef: ({ spawn }) => spawn(testMachine) as any,
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
      },
    },
    ImportingState: {
      initial: "DisplayingImportStateForm",
      on: {
        "user.cancelImportState": {
          target: "Open",
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
              target: "#appActor.Open",
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
          target: "Open",
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
              target: "#appActor.Open",
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
          target: "Open",
        },
      },
      states: {
        DisplayingUpdateSettingForm: {
          on: {
            "user.submitUpdateSettingForm": {
              target: "UpdatingSettings",
            },
          },
        },
        UpdatingSettings: {
          invoke: {
            id: "updateSettings",
            input: {},
            onDone: {
              target: "#appActor.Open",
            },
            onError: {
              target: "DisplayingUpdateSettingForm",
            },
            src: "updateSettings",
          },
        },
      },
    },
  },
});
