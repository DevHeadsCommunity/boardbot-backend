import { useToast } from "@/hooks/useToast";
import { Product } from "@/types";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useAppContext } from "./useAppContext";

export enum ProductState {
  Idle = "Idle",
  FetchingProducts = "FetchingProducts",
  DisplayingProducts = "DisplayingProducts.DisplayingProductsTable",
  DisplayingProduct = "DisplayingProducts.DisplayingProductsDetailModal",
  AddingProduct = "DisplayingProducts.DisplayingAddProductsForm",
}
export enum DisplayProductState {
  Idle = "Idle",
  DisplayingProduct = "DisplayingProducts.DisplayingProductsDetailModal",
  DisplayingUpdateProductForm = "DisplayingProducts.DisplayingProductsDetailModal.DisplayingUpdateProductForm",
  DisplayingDeleteProductForm = "DisplayingProducts.DisplayingProductsDetailModal.DisplayingDeleteProductForm",
  UpdatingProduct = "DisplayingProducts.DisplayingProductsDetailModal.DisplayingUpdateProductForm.UpdatingProduct",
  DeletingProduct = "DisplayingProducts.DisplayingProductsDetailModal.DisplayingDeleteProductForm.DeletingProduct",
}
export enum AddProductState {
  Idle = "Idle",
  DisplayingForm = "DisplayingProducts.DisplayingAddProductsForm",
  AddingProduct = "DisplayingProducts.DisplayingAddProductsForm.AddingProduct",
  AddingProductFormRawData = "DisplayingProducts.DisplayingAddProductsForm.AddingProductFormRawData",
  AddingProductsFormRawData = "DisplayingProducts.DisplayingAddProductsForm.AddingProductsFormRawData",
}

export const useProductContext = () => {
  const { actorRef } = useAppContext();
  const productActorRef = actorRef.product;
  const productActorState = useSelector(productActorRef, (state) => state);
  useToast(productActorRef);

  // const productState = useMemo(() => {
  //   if (!productActorState) return ProductState.Idle;
  //   console.log("productActorState:", productActorState);
  //   const currentState = productActorState.value as string;
  //   console.log("currentState:", currentState);
  //   return (
  //     (Object.keys(ProductState).find((key) => {
  //       console.log("key:", key);
  //       console.log("ProductState[key as keyof typeof ProductState]:", ProductState[key as keyof typeof ProductState]);
  //       console.log("check:", ProductState[key as keyof typeof ProductState] === currentState);

  //       return ProductState[key as keyof typeof ProductState] === currentState;
  //     }) as ProductState) || ProductState.Idle
  //   );
  // }, [productActorState]);

  // const appState: AppState = useSelector(appActorRef, (state) => {
  //   console.log(`state++: ${JSON.stringify(state.value)}`);
  //   for (const key in AppState) {
  //     if (state.matches(AppState[key as keyof typeof AppState] as any)) {
  //       return AppState[key as keyof typeof AppState];
  //     }
  //   }
  //   throw new Error(`Invalid app state: ${state.value}`);
  // });

  const productState = useMemo(() => {
    if (!productActorState) return ProductState.Idle;
    for (const key in ProductState) {
      if (productActorState.matches(ProductState[key as keyof typeof ProductState] as any)) {
        return ProductState[key as keyof typeof ProductState];
      }
    }
    throw new Error(`Invalid product state: ${productActorState.value}`);
  }, [productActorState]);

  // const displayProductState = useMemo(() => {
  //   if (productState !== ProductState.DisplayingProduct) return DisplayProductState.Idle;
  //   const currentState = productActorState.value as string;
  //   return (
  //     (Object.keys(DisplayProductState).find((key) => DisplayProductState[key as keyof typeof DisplayProductState] === currentState) as DisplayProductState) ||
  //     DisplayProductState.Idle
  //   );
  // }, [productActorState, productState]);

  const displayProductState = useMemo(() => {
    if (productState !== ProductState.DisplayingProduct) return DisplayProductState.Idle;
    for (const key in DisplayProductState) {
      if (productActorState.matches(DisplayProductState[key as keyof typeof DisplayProductState] as any)) {
        return DisplayProductState[key as keyof typeof DisplayProductState];
      }
    }
    throw new Error(`Invalid display product state: ${productActorState.value}`);
  }, [productActorState, productState]);

  // const addProductState = useMemo(() => {
  //   if (productState !== ProductState.AddingProduct) return AddProductState.Idle;
  //   const currentState = productActorState.value as string;
  //   return (Object.keys(AddProductState).find((key) => AddProductState[key as keyof typeof AddProductState] === currentState) as AddProductState) || AddProductState.Idle;
  // }, [productActorState, productState]);

  const addProductState = useMemo(() => {
    if (productState !== ProductState.AddingProduct) return AddProductState.Idle;
    for (const key in AddProductState) {
      if (productActorState.matches(AddProductState[key as keyof typeof AddProductState] as any)) {
        return AddProductState[key as keyof typeof AddProductState];
      }
    }
    throw new Error(`Invalid add product state: ${productActorState.value}`);
  }, [productActorState, productState]);

  const handleSelectProduct = useCallback(
    (product: Product) => {
      productActorRef?.send({ type: "user.selectProduct", product });
    },
    [productActorRef]
  );
  const handleSelectUpdateProduct = useCallback(() => {
    productActorRef?.send({ type: "user.selectUpdateProduct" });
  }, [productActorRef]);
  const handleSelectDeleteProduct = useCallback(() => {
    productActorRef?.send({ type: "user.selectDeleteProduct" });
  }, [productActorRef]);
  const handleSubmitDeleteProduct = useCallback(
    (productName: string) => {
      productActorRef?.send({ type: "user.submitDeleteProduct", productName });
    },
    [productActorRef]
  );
  const handleSubmitUpdateProduct = useCallback(
    (productData: Partial<Product>) => {
      productActorRef?.send({ type: "user.submitUpdateProduct", productData });
    },
    [productActorRef]
  );
  const handleCancelProductUpdate = useCallback(() => {
    productActorRef?.send({ type: "user.cancelProductUpdate" });
  }, [productActorRef]);
  const handleCloseProductDetailModal = useCallback(() => {
    productActorRef?.send({ type: "user.closeProductDetailModal" });
  }, [productActorRef]);

  const handleAddProducts = useCallback(() => {
    productActorRef?.send({ type: "user.addProducts" });
  }, [productActorRef]);
  const handleSubmitAddProduct = useCallback(
    (productData: Product) => {
      productActorRef?.send({ type: "user.submitAddProduct", productData });
    },
    [productActorRef]
  );
  const handleSubmitAddProductRawData = useCallback(
    (productId: string, rawData: string) => {
      productActorRef?.send({ type: "user.submitAddProductRawData", productId, rawData });
    },
    [productActorRef]
  );
  const handleSubmitAddProductsRawData = useCallback(
    (file: File) => {
      productActorRef?.send({ type: "user.submitAddProductsRawData", file });
    },
    [productActorRef]
  );
  const handleCancelAddProduct = useCallback(() => {
    productActorRef?.send({ type: "user.cancelAddProduct" });
  }, [productActorRef]);
  const handleCloseAddProducts = useCallback(() => {
    productActorRef?.send({ type: "user.closeAddProducts" });
  }, [productActorRef]);

  return {
    state: {
      productState,
      displayProductState,
      addProductState,
    },
    data: {
      product: useSelector(productActorRef, (state) => state?.context.product || null),
      products: useSelector(productActorRef, (state) => state?.context.products || []),
    },
    actions: {
      click: {
        selectProduct: handleSelectProduct,
        selectUpdateProduct: handleSelectUpdateProduct,
        selectDeleteProduct: handleSelectDeleteProduct,
        addProducts: handleAddProducts,
      },
      submit: {
        deleteProduct: handleSubmitDeleteProduct,
        updateProduct: handleSubmitUpdateProduct,
        addProduct: handleSubmitAddProduct,
        addProductRawData: handleSubmitAddProductRawData,
        addProductsRawData: handleSubmitAddProductsRawData,
      },
      close: {
        productDetailModal: handleCloseProductDetailModal,
        addProducts: handleCloseAddProducts,
      },
      cancel: {
        productUpdate: handleCancelProductUpdate,
        addProduct: handleCancelAddProduct,
      },
    },
  };
};

export type ProductData = ReturnType<typeof useProductContext>["data"];
export type ProductActions = ReturnType<typeof useProductContext>["actions"];
