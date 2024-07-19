import { setup } from "xstate";

export const chatMachine = setup({
  types: {
    context: {} as {},
    events: {} as
      | { type: "app.startChat" }
      | { type: "app.stopChat" },
  },
  guards: {
  },
}).createMachine({
  context: {},
  id: "chatActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "app.startChat": {
          target: "DisplayingChat",
        },
      },
    },
    DisplayingChat: {
      on: {
        "app.stopChat": {
          target: "idle",
        },
      },
    },
  },
});
