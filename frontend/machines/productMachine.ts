import { apiCall } from "@/lib/api";
import { Product, productFromJson, ProductSchema, productToJson } from "@/types";
import { ActorRefFrom, assign, ContextFrom, emit, fromPromise, setup } from "xstate";
import { z } from "zod";

const PAGE_SIZE = 20; // Number of products per page

const ProductMachineContextSchema = z.object({
  product: ProductSchema.optional(),
  products: z.array(ProductSchema),
  currentPage: z.number(),
  totalProducts: z.number(),
  filter: z.record(z.string(), z.string()).optional(),
});

type ProductMachineContext = z.infer<typeof ProductMachineContextSchema>;

export const productMachine = setup({
  types: {
    context: {} as ProductMachineContext,
    events: {} as
      | { type: "app.startManagingProducts" }
      | { type: "app.stopManagingProducts" }
      | { type: "user.addProducts" }
      | { type: "user.selectProduct"; product: Product }
      | { type: "user.closeAddProducts" }
      | { type: "user.closeProductDetailModal" }
      | { type: "user.selectUpdateProduct" }
      | { type: "user.selectDeleteProduct" }
      | { type: "user.submitDeleteProduct"; productId: string }
      | { type: "user.submitUpdateProduct"; productData: Product }
      | { type: "user.cancelProductUpdate" }
      | { type: "user.submitAddProduct"; productData: Product }
      | { type: "user.submitAddProductRawData"; productId: string; rawData: string }
      | { type: "user.submitAddProductsRawData"; file: File }
      | { type: "user.cancelAddProduct" }
      | { type: "user.nextPage" }
      | { type: "user.previousPage" }
      | { type: "user.applyFilter"; filter: Record<string, string> },
  },
  actors: {
    productUpdater: fromPromise(async ({ input }: { input: { productId: string; productData: Product } }) => {
      const response = await apiCall("PUT", `/products/${input.productId}`, productToJson(input.productData));
      return productFromJson(response);
    }),
    productDeleter: fromPromise(async ({ input }: { input: { productId: string } }) => {
      await apiCall("DELETE", `/products/${input.productId}`);
      return input.productId;
    }),
    productAdder: fromPromise(async ({ input }: { input: { productData: Product } }) => {
      const response = await apiCall("POST", "/products", productToJson(input.productData));
      return productFromJson(response);
    }),
    rawProductAdder: fromPromise(async ({ input }: { input: { rawData: string } }) => {
      const response = await apiCall("POST", "/products/raw", { rawData: input.rawData });
      return productFromJson(response);
    }),
    rawProductsAdder: fromPromise(async ({ input }: { input: { file: File } }) => {
      const formData = new FormData();
      formData.append("file", input.file);
      const response = await apiCall("POST", "/products/batch", formData);
      return response.map(productFromJson);
    }),
    productsFetcher: fromPromise(async ({ input }: { input: { page: number; pageSize: number; filter?: Record<string, string> } }) => {
      const queryParams = new URLSearchParams({
        page: input.page.toString(),
        pageSize: input.pageSize.toString(),
        ...(input.filter || {}),
      });
      const response = await apiCall("GET", `/products?${queryParams.toString()}`);
      return {
        products: response.products.map(productFromJson),
        totalProducts: response.total,
      };
    }),
  },
  guards: {
    canGoToNextPage: ({ context }) => (context.currentPage + 1) * PAGE_SIZE < context.totalProducts,
    canGoToPreviousPage: ({ context }) => context.currentPage > 0,
  },
}).createMachine({
  context: ProductMachineContextSchema.parse({
    product: undefined,
    products: [],
    currentPage: 0,
    totalProducts: 0,
    filter: undefined,
  }),
  id: "productActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "app.startManagingProducts": {
          target: "displayingProducts",
        },
      },
    },
    displayingProducts: {
      initial: "fetchingProducts",
      on: {
        "app.stopManagingProducts": {
          target: "idle",
        },
      },
      states: {
        fetchingProducts: {
          invoke: {
            id: "productsFetcher",
            input: ({ context }) => ({
              page: context.currentPage,
              pageSize: PAGE_SIZE,
              filter: context.filter,
            }),
            onDone: {
              target: "displayingProductsTable",
              actions: assign({
                products: ({ event }) => event.output.products,
                totalProducts: ({ event }) => event.output.totalProducts,
              }),
            },
            onError: {
              target: "#productActor.idle",
              actions: emit({
                type: "notification",
                data: {
                  type: "error",
                  message: "Failed to fetch products",
                },
              }),
            },
            src: "productsFetcher",
          },
        },
        displayingProductsTable: {
          on: {
            "user.selectProduct": {
              target: "displayingProductsDetailModal",
              actions: assign({ product: ({ event }) => event.product }),
            },
            "user.addProducts": {
              target: "displayingAddProductsForm",
            },
            "user.nextPage": {
              target: "fetchingProducts",
              actions: assign({
                currentPage: ({ context }) => context.currentPage + 1,
              }),
              guard: {
                type: "canGoToNextPage",
              },
            },
            "user.previousPage": {
              target: "fetchingProducts",
              actions: assign({
                currentPage: ({ context }) => context.currentPage - 1,
              }),
              guard: {
                type: "canGoToPreviousPage",
              },
            },
            "user.applyFilter": {
              target: "fetchingProducts",
              actions: assign({
                filter: ({ event }) => event.filter,
                currentPage: 0,
              }),
            },
          },
        },
        displayingProductsDetailModal: {
          initial: "displayingProduct",
          on: {
            "user.closeProductDetailModal": {
              target: "displayingProductsTable",
            },
            "user.cancelProductUpdate": {
              target: "#productActor.displayingProducts.displayingProductsDetailModal.displayingProduct",
            },
          },
          states: {
            displayingProduct: {
              on: {
                "user.selectUpdateProduct": {
                  target: "displayingUpdateProductForm",
                },
                "user.selectDeleteProduct": {
                  target: "displayingDeleteProductForm",
                },
              },
            },
            displayingUpdateProductForm: {
              on: {
                "user.submitUpdateProduct": {
                  target: "updatingProduct",
                },
              },
            },
            displayingDeleteProductForm: {
              on: {
                "user.submitDeleteProduct": {
                  target: "deletingProduct",
                },
              },
            },
            updatingProduct: {
              invoke: {
                id: "productUpdater",
                input: ({ context, event }) => {
                  if (!context.product) {
                    throw new Error("No product selected");
                  }
                  if (event.type !== "user.submitUpdateProduct") {
                    throw new Error("Invalid event");
                  }
                  return {
                    productId: context.product.ids,
                    productData: event.productData,
                  };
                },
                onDone: {
                  target: "displayingProduct",
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
                  target: "displayingUpdateProductForm",
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
            deletingProduct: {
              invoke: {
                id: "productDeleter",
                input: ({ context }) => ({
                  productId: context.product?.id!,
                }),
                onDone: {
                  target: "#productActor.displayingProducts.fetchingProducts",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "success",
                      message: "Product deleted successfully",
                    },
                  }),
                },
                onError: {
                  target: "displayingDeleteProductForm",
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
        displayingAddProductsForm: {
          initial: "displayingForm",
          on: {
            "user.closeAddProducts": {
              target: "displayingProductsTable",
            },
            "user.cancelAddProduct": {
              target: "#productActor.displayingProducts.displayingAddProductsForm.displayingForm",
            },
          },
          states: {
            displayingForm: {
              on: {
                "user.submitAddProduct": {
                  target: "addingProduct",
                },
                "user.submitAddProductRawData": {
                  target: "addingProductFormRawData",
                },
                "user.submitAddProductsRawData": {
                  target: "addingProductsFormRawData",
                },
              },
            },
            addingProduct: {
              invoke: {
                id: "productAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProduct") throw new Error("Invalid event type");
                  return { productData: event.productData };
                },
                onDone: {
                  target: "#productActor.displayingProducts.fetchingProducts",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "success",
                      message: "Product added successfully",
                    },
                  }),
                },
                onError: {
                  target: "displayingForm",
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
            addingProductFormRawData: {
              invoke: {
                id: "rawProductAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProductRawData") throw new Error("Invalid event type");
                  return { rawData: event.rawData };
                },
                onDone: {
                  target: "#productActor.displayingProducts.fetchingProducts",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "success",
                      message: "Product added successfully",
                    },
                  }),
                },
                onError: {
                  target: "displayingForm",
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
            addingProductsFormRawData: {
              invoke: {
                id: "rawProductsAdder",
                input: ({ event }) => {
                  if (event.type !== "user.submitAddProductsRawData") throw new Error("Invalid event type");
                  return { file: event.file };
                },
                onDone: {
                  target: "#productActor.displayingProducts.fetchingProducts",
                  actions: emit({
                    type: "notification",
                    data: {
                      type: "success",
                      message: "Products added successfully",
                    },
                  }),
                },
                onError: {
                  target: "displayingForm",
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
  },
});

export const serializeProductState = (productRef: ActorRefFrom<typeof productMachine>) => {
  const snapshot = productRef.getSnapshot();
  return {
    products: snapshot.context.products,
    currentPage: snapshot.context.currentPage,
    totalProducts: snapshot.context.totalProducts,
    filter: snapshot.context.filter,
    currentState: snapshot.value,
  };
};

export const deserializeProductState = (savedState: unknown): ContextFrom<typeof productMachine> => {
  const parsedState = ProductMachineContextSchema.parse(savedState);
  return {
    ...parsedState,
    product: undefined, // Reset selected product on deserialization
  };
};
