import { apiCall } from "@/lib/api";
import { Product, productFromJson, ProductSchema, productToJson } from "@/types";
import Papa from "papaparse";
import { ActorRefFrom, assign, ContextFrom, emit, fromPromise, setup } from "xstate";
import { z } from "zod";

const PAGE_SIZE = 20; // Number of products per page

export enum FeatureExtractorType {
  Simple = "simple",
  Agentic = "agentic",
}

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
      | { type: "user.submitDeleteProduct"; id: string }
      | { type: "user.submitUpdateProduct"; productData: Product }
      | { type: "user.cancelProductUpdate" }
      | { type: "user.submitAddProduct"; productData: Product }
      | {
          type: "user.submitAddProductRawData";
          productId: string;
          rawData: string;
          maxMissingFeatureAttempts: number;
          maxLowConfidenceAttempts: number;
          maxNoProgressAttempts: number;
          confidenceThreshold: number;
        }
      | {
          type: "user.submitAddProductsRawData";
          file: File;
          maxMissingFeatureAttempts: number;
          maxLowConfidenceAttempts: number;
          maxNoProgressAttempts: number;
          confidenceThreshold: number;
          batchSize: number;
        }
      | { type: "user.cancelAddProduct" }
      | { type: "user.nextPage" }
      | { type: "user.previousPage" }
      | { type: "user.applyFilter"; filter: Record<string, string> },
  },
  actors: {
    productUpdater: fromPromise(async ({ input }: { input: { id: string; productData: Product } }) => {
      console.log("+++ productUpdater id", input.id);
      console.log("+++ productUpdater input", productToJson(input.productData));
      const response = await apiCall("PUT", `/products/${input.id}`, productToJson(input.productData));
      if (response.message) return input.productData;
      throw new Error("Failed to update product");
    }),
    productDeleter: fromPromise(async ({ input }: { input: { id: string } }) => {
      const response = await apiCall("DELETE", `/products/${input.id}`);
      if (response.message) return response;
      throw new Error("Failed to delete product");
    }),
    productAdder: fromPromise(async ({ input }: { input: { productData: Product } }) => {
      const response = await apiCall("POST", "/products", productToJson(input.productData));
      if (response.id) return response;
      throw new Error("Failed to add product");
    }),
    rawProductAdder: fromPromise(
      async ({
        input,
      }: {
        input: {
          product_id: string;
          raw_data: string;
          max_missing_feature_attempts: number;
          max_low_confidence_attempts: number;
          max_no_progress_attempts: number;
          confidence_threshold: number;
        };
      }) => {
        const response = await apiCall("POST", "/products/raw", input);
        if (response.id) return response;
        throw new Error("Failed to add product from raw data");
      }
    ),
    rawProductsAdder: fromPromise(
      async ({
        input,
      }: {
        input: {
          file: File;
          max_missing_feature_attempts: number;
          max_low_confidence_attempts: number;
          max_no_progress_attempts: number;
          confidence_threshold: number;
          batch_size: number;
        };
      }) => {
        return new Promise((resolve, reject) => {
          Papa.parse(input.file, {
            complete: async (results) => {
              if (results.errors.length > 0) {
                reject(new Error("CSV parsing failed"));
                return;
              }
              const products = results.data.map((row: any) => ({
                product_id: row.product_id,
                raw_data: row.raw_data,
              }));
              const batchInput = {
                products: products,
                batch_size: input.batch_size,
                max_missing_feature_attempts: input.max_missing_feature_attempts,
                max_low_confidence_attempts: input.max_low_confidence_attempts,
                max_no_progress_attempts: input.max_no_progress_attempts,
                confidence_threshold: input.confidence_threshold,
              };

              try {
                const response = await apiCall("POST", "/products/batch/raw", batchInput);
                if (response.products) {
                  resolve(response);
                } else {
                  reject(new Error("Failed to add products from CSV"));
                }
              } catch (error) {
                reject(error);
              }
            },
            header: true,
            skipEmptyLines: true,
          });
        });
      }
    ),
    productsFetcher: fromPromise(async ({ input }: { input: { page: number; pageSize: number; filter?: Record<string, string> } }) => {
      const queryParams = new URLSearchParams({
        page: (input.page + 1).toString(),
        page_size: input.pageSize.toString(),
      });

      if (input.filter && Object.keys(input.filter).length > 0) {
        queryParams.append("filter", JSON.stringify(input.filter));
      }

      const response = await apiCall("GET", `/products?${queryParams.toString()}`);
      console.log("response", response);
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
  /** @xstate-layout N4IgpgJg5mDOIC5QAcBOB7CBXAxgFwEF91UA6ASwgBswBiAQ2WVNj3tTwFl6A7eqcjygAFDNnywA2gAYAuohTpY5POXQ8FIAB6IArACYANCACeiABwBGUrunTL+ywGZ95gJwB2T04C+P42iYuITEZBDksMhU9CaCImLBsAxMLHjoyNx8AkKiQRIy8kggyEoqahpFOggALPpO0qQAbNXm1W7VltJWltXGZgiWXtZdXe761R6Nja1+AQn4RGlhEVExcbnieLCkAGZgeDgAFuvzW7QQ6mAUPABu6ADWV4GbsABi+0dgqAWaJcqq6k0VUs5mkuia1WkjX0Hnqbkc1ScfUQMIaHjabksDlauicbnMulmxVOixIpHCkWisRyp22ewOxxpeTOXwwZFWeB2JAAtqRnol3gyvj8in8yoDKohavUIa12p1ur1TIhLI1PDZpK41bUJvoukT+QtQuSVlSTszthTVtT4haACr0ABGNFoWFgXxYYBo+A2wRFin+5SBKsm4OaUJhcIRSOVCExDTcTi8LV0ll05g8aYNJONVrNTJeJspawLiQdzrobo99AgEF9+Tkv1KAIqoCqnmRCH0bkapHMrR65kaSb1+OzzNJy2LNvrWyL1vNL3LLqrZB4YC0eGE-DA-uKzaDkoGoLDkOhsOk8J6Mf6HScpGkTjGWJ79iT482k-n+dthbzJd-MsnRXd12VQMAbjUN1txgPcxRbYMBi8U8IwvK9EU7Ww3CaQY9UGRFmnRRoP2CL9-xnWlvwA2dYGXStQNIRgohMV5yCoPBhUbUUDwlNsQwJCFUKja9O0aKFSEsNxdBafRu2xBwSKNJYqIoi0VMXRIABF9noNjOEwegqFdBicCoJQwFnbS2D0gyqDgnjW20EMPBQ89hIw2MPFhB86nRXRoQJPFCX8YkJ1zU1qMo8iNIkKzdKofSIEM4yPRwXgcC9WcAFVkCSjj7MDXinIGNx2lIJxEUmaZqgI3QPE7dpewmDxpEzOrEwcNxFJCZTotLCR1P6rY4pspKqEGwD8BSsh3W9PAcryizTgK8VHKqcYJiaKT6lhXzL07Tp0z7AwRhBapbFa7qyIi1S-xumLhp00bDIm2dps9ObtJoDjZxWhCjw2jwttxVqXCTfbYwcTVSETN8atcST2iu8Lpwey17qG2ARoS2yJoW+gftOV4eXe2AsEdbkVHxwnmT+w8+K7TwgeqMT2jaVrYXxA6HHBHbJnMOpoX0YK5jC3qMcmuc+slrGnpxsaJq+-YluZYnUG5UnycpvAlZpzY6aK9amdIFnLxqtwObxcwDv0NVyoJAXxi8eF3xCw0erJaWaNe2lscSl6sFygmHvOS5rjuR4+VOanOMKANVsQ+pXBN7tCKfVpNSVfoLfvTU8TfDwBZa-RkfF1HMZ9i0-dxwO8pD1kyQ5Ll1aj5kY++Lj4-+hmk+w226uF6FOlkm8VUfawPG7dEBxcLzS89iXva9325f98aIC9fYQ4uddw4eJ5Tl12Om0KtbECcMTzHKxoL2HUdXG5zFSEnmr0xvvE1XnqcFwr5eq9X3GG9vr11QGyPk0ROQ8lbpsI+Hc477lPonR81Ryqpn8k4SSklJ71UhoMcEoJC6akaP5TwxE3Y5jLj-GWE0CC1homrDWq5SCmXMrQustIDZnwGPUawQ4LypivMQzCj4HzuFKniTEUk6pf0rndcuUA2H0JJkwtKPAMpUEUctTuCCE5HmcEYWMBhhhTB6B1C+LMZF-zkVQzRFoGETQYZrCmKhbH620fBemxU6q8J5iDEYGZMJeGfg4eoapSqphhJYxeUUJauIFFA6WjimFk2cYQOhpwABK9AADumkCb0E4YhbxfZfH1H8Tg-ok97xeEfI0BwiJHBZnIWLBe8il6xPSXYhJEskkMRSdrOJEgsm5PyYUo8xSrDCz8aCAJsY+F9mqmmFoaph5RLaTE+Rgytj2JrOEIaodd6CAjgfCctZj7cUQXonhCz+GSUcEIyGVsbA9laGqMY9g1lUPaZszpLwdm1hAWApuUD3ZsPOV3TxVRqqkARkmNMGZ+zok7MsiSFVXCZlDMQy6zTPwoy+Rsmxvz4kt12Q9Bhwy8lsAOVcI5+9SCoBybOMFcCT66IZp1Xh78wR3NVLoA6bR9ASWnlMSZg4yGi1xZQn83zCXsK6SSgFQ1yU5MpfQWgDd2QQObryBl2SmVnJZRctlxUpiCowcLFyUJOZOD5bGYcDRHB1A6LUIhT5PnSoJT+LZbwoGksxsqkZVKd40tuHS3VNFmVjPZQjG59QBH3Ntf0eF4IXKuCHMOLCw53WRTUtLb1-y9kywDaq9VoDG5aqgeG2kkb3EOUQsQ-BiILa6HTFiOpWdEBeRQd2R8Ukpgf2Fn4EKPBMBwF+BQkgrLu7FQALQOE7DO8VoVJVkkoDQKdkKpQCphe4Zwth7l1AOpPQV0gOhDkda2rqOLSJ4o9RaDdhtz6NAOuYe8ws3yBUTC2wd16lKtPxWpekRw0YPq4U+PEMLahT0wcOAkokegPkhNy3QiZiGyWzbdRIsigIVlA4hNMGCHyJlfXU5ow9OxxpNjfFoXlQY2uxRKm9Uqc3WLvS8auY08N6MauVSqIqaoXzqp2Kw4IDBJlBKe+EzaMNo2w7FABCsrHBC4wzWSLQqOXj2i5Quo84wsxhrRtqXhzVXsY3+7+bGsNKfk9ZeWL1pYx1nAwlTxVbb4mfrCVMUJWaTAOmCbCNq9SgjOhdDwMnf7RP-rZteitN562CM5o1071rF2fq+gkw8v09BtiIxEcNahWFKtUcL1DrOPWizXIOqghouaqGDFB+csUOEknUvzLhn7TDqShqwGZEQlZlZZmz8UYtAK3jVpLm6EBg17FiSe1421uEfg6jNdhcQ1WHGF39HsLMsasx0uVfyeS1YsB2qb7nhwdGIa0FygVitbeuus3N+2lEt0SUdibj6pvQioxmS8Lh0yvukphRwNgTFtAweYpdoLb27YGnmolEgC0PWOwgdw94c6pvTaelDwiGjpnxNMAk7RpIi2XUx-9g2pbPdpEjpVPIKX5JRxmPudV+wZebaJGqTRpi9qni5VU-XPUAXzb6xVRb6cqsZx9rhGZeyswIk+dq8JOyFyvkRP70kei2Du34IAA */
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
                currentPage: ({ context }) => Math.max(0, context.currentPage - 1),
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
                    id: context.product.id,
                    productData: event.productData,
                  };
                },
                onDone: {
                  target: "displayingProduct",
                  actions: [
                    assign({
                      product: ({ event }) => event.output,
                      products: ({ context, event }) => context.products.map((p) => (p.id === event.output.id ? event.output : p)),
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
                  id: context.product?.id!,
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
                  return {
                    product_id: event.productId,
                    raw_data: event.rawData,
                    max_missing_feature_attempts: event.maxMissingFeatureAttempts,
                    max_low_confidence_attempts: event.maxLowConfidenceAttempts,
                    max_no_progress_attempts: event.maxNoProgressAttempts,
                    confidence_threshold: event.confidenceThreshold,
                  };
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
                  return {
                    file: event.file,
                    max_missing_feature_attempts: event.maxMissingFeatureAttempts,
                    max_low_confidence_attempts: event.maxLowConfidenceAttempts,
                    max_no_progress_attempts: event.maxNoProgressAttempts,
                    confidence_threshold: event.confidenceThreshold,
                    batch_size: event.batchSize,
                  };
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
