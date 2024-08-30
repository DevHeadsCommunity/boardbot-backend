import { apiCall } from "@/lib/api";
import { Product, ProductFromJson } from "@/types";
import { ActorRefFrom, assign, ContextFrom, emit, fromPromise, setup } from "xstate";

export const productMachine = setup({
  types: {
    context: {} as {
      product: Product;
      products: Product[];
    },
    events: {} as
      | { type: "app.updateState" }
      | { type: "user.addProducts" }
      | { type: "user.selectProduct"; product: Product }
      | { type: "user.closeAddProducts" }
      | { type: "app.stopManagingProducts" }
      | { type: "app.startManagingProducts" }
      | { type: "user.closeProductDetailModal" }
      | { type: "user.selectUpdateProduct" }
      | { type: "user.selectDeleteProduct" }
      | { type: "user.submitDeleteProduct"; productName: string }
      | { type: "user.submitUpdateProduct"; productData: Partial<Product> }
      | { type: "user.cancelProductUpdate" }
      | { type: "user.submitAddProduct"; productData: Product }
      | { type: "user.submitAddProductRawData"; productId: string; rawData: string }
      | { type: "user.submitAddProductsRawData"; file: File }
      | { type: "user.cancelAddProduct" },
  },
  actors: {
    productUpdater: fromPromise(async ({ input }: { input: { productName: string; productData: Partial<Product> } }) => {
      try {
        return await apiCall("PUT", `/products/${input.productName}`, input.productData);
      } catch (error) {
        throw error;
      }
    }),
    productDeleter: fromPromise(async ({ input }: { input: { productName: string } }) => {
      try {
        return await apiCall("DELETE", `/products/${input.productName}`);
      } catch (error) {
        throw error;
      }
    }),
    productAdder: fromPromise(async ({ input }: { input: { productData: Product } }) => {
      try {
        return await apiCall("POST", "/products", input.productData);
      } catch (error) {
        throw error;
      }
    }),
    rawProductAdder: fromPromise(async ({ input }: { input: { rawData: string } }) => {
      try {
        return await apiCall("POST", "/products/raw", { rawData: input.rawData });
      } catch (error) {
        throw error;
      }
    }),
    rawProductsAdder: fromPromise(async ({ input }: { input: { file: File } }) => {
      try {
        const formData = new FormData();
        formData.append("file", input.file);
        return await apiCall("POST", "/products/batch", formData);
      } catch (error) {
        throw error;
      }
    }),
    fetchProduct: fromPromise(async ({ input }: { input: { productName: string } }) => {
      try {
        const result = await apiCall("GET", `/products/${input.productName}`);
        console.log("result ::: ", result);
        return ProductFromJson(result.product.data.get.product);
      } catch (error) {
        throw error;
      }
    }),
    fetchProducts: fromPromise(async () => {
      try {
        const result = await apiCall("GET", "/products");
        console.log("result ::: ", result);
        const products = result.products.map(ProductFromJson);
        return { products };
      } catch (error) {
        throw error;
      }
    }),
  },
  guards: {
    productsExist: ({ context }) => context.products.length > 0,
  },
}).createMachine({
  context: {
    product: {} as Product,
    products: [] as Product[],
  },
  id: "productActor",
  initial: "idle",
  on: {
    "app.updateState": {},
  },
  states: {
    idle: {
      on: {
        "app.startManagingProducts": [
          {
            target: "DisplayingProducts",
            guard: {
              type: "productsExist",
            },
          },
          {
            target: "FetchingProducts",
          },
        ],
      },
    },
    DisplayingProducts: {
      initial: "DisplayingProductsTable",
      on: {
        "app.stopManagingProducts": {
          target: "idle",
        },
      },
      states: {
        DisplayingProductsTable: {
          on: {
            "user.selectProduct": {
              target: "DisplayingProductsDetailModal",
              actions: assign({
                product: ({ event }) => event.product,
              }),
            },
            "user.addProducts": {
              target: "DisplayingAddProductsForm",
            },
          },
        },
        DisplayingProductsDetailModal: {
          initial: "DisplayingProduct",
          on: {
            "user.closeProductDetailModal": {
              target: "DisplayingProductsTable",
            },
            "user.cancelProductUpdate": {
              target: "#productActor.DisplayingProducts.DisplayingProductsDetailModal.DisplayingProduct",
            },
          },
          states: {
            DisplayingProduct: {
              on: {
                "user.selectUpdateProduct": {
                  target: "DisplayingUpdateProductForm",
                },
                "user.selectDeleteProduct": {
                  target: "DisplayingDeleteProductForm",
                },
              },
            },
            DisplayingUpdateProductForm: {
              on: {
                "user.submitUpdateProduct": {
                  target: "UpdatingProduct",
                },
              },
            },
            DisplayingDeleteProductForm: {
              on: {
                "user.submitDeleteProduct": {
                  target: "DeletingProduct",
                },
              },
            },
            UpdatingProduct: {
              invoke: {
                id: "productUpdater",
                input: ({ context, event }) => {
                  if (event.type !== "user.submitUpdateProduct") throw new Error("Invalid event type");
                  return {
                    productName: context.product.name,
                    productData: event.productData,
                  };
                },
                onDone: {
                  target: "DisplayingProduct",
                  actions: [
                    assign({
                      product: ({ event }) => event.output,
                      products: ({ context, event }) => context.products.map((p) => (p.ids === event.output.ids ? event.output : p)),
                    }),
                    emit({
                      type: "notification",
                      data: {
                        type: "success",
                        message: "Product updated successfully",
                      },
                    }),
                  ],
                },
                onError: {
                  target: "DisplayingUpdateProductForm",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "error",
                      message: "Failed to update product",
                    },
                  }),
                },
                src: "productUpdater",
              },
            },
            DeletingProduct: {
              invoke: {
                id: "productDeleter",
                input: ({ context }) => ({
                  productName: context.product.name,
                }),
                onDone: {
                  target: "#productActor.DisplayingProducts.DisplayingProductsTable",
                  actions: [
                    assign({
                      products: ({ context }) => context.products.filter((p) => p.ids !== context.product.ids),
                    }),
                    emit({
                      type: "notification",
                      data: {
                        type: "success",
                        message: "Product deleted successfully",
                      },
                    }),
                  ],
                },
                onError: {
                  target: "DisplayingDeleteProductForm",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "error",
                      message: "Failed to delete product",
                    },
                  }),
                },
                src: "productDeleter",
              },
            },
          },
        },
        DisplayingAddProductsForm: {
          initial: "DisplayingForm",
          on: {
            "user.closeAddProducts": {
              target: "DisplayingProductsTable",
            },
            "user.cancelAddProduct": {
              target: "#productActor.DisplayingProducts.DisplayingAddProductsForm.DisplayingForm",
            },
          },
          states: {
            DisplayingForm: {
              on: {
                "user.submitAddProduct": {
                  target: "AddingProduct",
                },
                "user.submitAddProductRawData": {
                  target: "AddingProductFormRawData",
                },
                "user.submitAddProductsRawData": {
                  target: "AddingProductsFormRawData",
                },
              },
            },
            AddingProduct: {
              invoke: {
                id: "productAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProduct") throw new Error("Invalid event type");
                  return {
                    productData: event.productData,
                  };
                },
                onDone: {
                  target: "#productActor.DisplayingProducts.DisplayingProductsTable",
                  actions: [
                    assign({
                      products: ({ context, event }) => [...context.products, event.output],
                    }),
                    emit({
                      type: "notification",
                      data: {
                        type: "success",
                        message: "Product added successfully",
                      },
                    }),
                  ],
                },
                onError: {
                  target: "DisplayingForm",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "error",
                      message: "Failed to add product",
                    },
                  }),
                },
                src: "productAdder",
              },
            },
            AddingProductFormRawData: {
              invoke: {
                id: "rawProductAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProductRawData") throw new Error("Invalid event type");
                  return {
                    rawData: event.rawData,
                  };
                },
                onDone: {
                  target: "#productActor.DisplayingProducts.DisplayingProductsTable",
                  actions: [
                    assign({
                      products: ({ context, event }) => [...context.products, event.output],
                    }),
                    emit({
                      type: "notification",
                      data: {
                        type: "success",
                        message: "Product added successfully",
                      },
                    }),
                  ],
                },
                onError: {
                  target: "DisplayingForm",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "error",
                      message: "Failed to add product from raw data",
                    },
                  }),
                },
                src: "rawProductAdder",
              },
            },
            AddingProductsFormRawData: {
              invoke: {
                id: "rawProductsAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProductsRawData") throw new Error("Invalid event type");
                  return {
                    file: event.file,
                  };
                },
                onDone: {
                  target: "#productActor.DisplayingProducts.DisplayingProductsTable",
                  actions: [
                    assign({
                      products: ({ context, event }) => [...context.products, ...event.output],
                    }),
                    emit({
                      type: "notification",
                      data: {
                        type: "success",
                        message: "Products added successfully",
                      },
                    }),
                  ],
                },
                onError: {
                  target: "DisplayingForm",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "error",
                      message: "Failed to add products from CSV",
                    },
                  }),
                },
                src: "rawProductsAdder",
              },
            },
          },
        },
      },
    },
    FetchingProducts: {
      invoke: {
        input: {},
        onDone: {
          target: "DisplayingProducts",
          actions: assign({
            products: ({ event }) => event.output.products,
          }),
        },
        onError: {
          target: "idle",
          actions: emit({
            type: "notification",
            data: {
              type: "error",
              message: "Failed to fetch products",
            },
          }),
        },
        src: "fetchProducts",
      },
    },
  },
});

export const serializeProductState = (productRef: ActorRefFrom<typeof productMachine>) => {
  const snapshot = productRef.getSnapshot();
  return {
    currentState: snapshot.value,
  };
};

export const deserializeProductState = (savedState: any): ContextFrom<typeof productMachine> => {
  return {
    ...savedState,
  };
};
