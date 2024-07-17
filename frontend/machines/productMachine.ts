import { setup } from "xstate";

export const productMachine = setup({
  types: {
    context: {} as {},
    events: {} as
      | { type: "app.startManagingProducts" }
      | { type: "app.stopManagingProducts" },
  },
}).createMachine({
  context: {},
  id: "productActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "app.stopManagingProducts": {
          target: "DisplayingProducts",
        },
      },
    },
    DisplayingProducts: {
      on: {
        "app.startManagingProducts": {
          target: "idle",
        },
      },
    },
  },
});
