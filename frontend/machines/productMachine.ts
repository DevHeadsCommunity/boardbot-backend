import { ActorRefFrom, setup } from "xstate";

export const productMachine = setup({
  types: {
    context: {} as {},
    events: {} as { type: "app.startManagingProducts" } | { type: "app.stopManagingProducts" },
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

export const getProductMachineState = (productRef: ActorRefFrom<typeof productMachine>) => {
  const snapshot = productRef.getSnapshot();
  return {
    currentState: snapshot.value,
  };
};
