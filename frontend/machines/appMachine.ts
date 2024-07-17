import { assign, sendTo, setup } from "xstate";
import { chatMachine } from "./chatMachine";
import { productMachine } from './productMachine';
import { testMachine } from './testMachine';

export const machine = setup({
  types: {
    context: {} as {
      chatRef: null;
      testRef: null;
      prodRef: null;
    },
    events: {} as
      | { type: "user.selectChat" }
      | { type: "user.selectTest" }
      | { type: "user.selectManageProducts" },
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
      initial: "ManagingProducts",
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
      },
      entry: assign({
        chatRef: ({ spawn }) => spawn(chatMachine) as any,
        testRef: ({ spawn }) => spawn(testMachine) as any,
        prodRef: ({ spawn }) => spawn(productMachine) as any,
      }),
      states: {
        ManagingProducts: {
          entry: sendTo(({ context }) => context.chatRef!, {
            type: "app.startChat",
          } as any),
          exit: sendTo(({ context }) => context.chatRef!, {
            type: "app.stopChat",
          } as any),
        },
        Testing: {
          entry: sendTo(({ context }) => context.testRef!, {
            type: "app.startTest",
          } as any),
          exit: sendTo(({ context }) => context.testRef!, {
            type: "app.stopTest",
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
  },
});
