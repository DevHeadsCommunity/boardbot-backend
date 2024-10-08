import { convertStateToString } from "@/lib/stateToStr";
import { productMachine } from "@/machines/productMachine";
import { Product } from "@/types/productTypes";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useAppContext } from "./useAppContext";
import { useToast } from "./useToast";

export enum ProductState {
  Idle = "Idle",
  FetchingProducts = "FetchingProducts",
  DisplayingProductsTable = "DisplayingProductsTable",
  DisplayingProductsDetailModal = "DisplayingProductsDetailModal",
  DisplayingAddProductsForm = "DisplayingAddProductsForm",
}

export enum DisplayProductState {
  Idle = "Idle",
  DisplayingProduct = "DisplayingProduct",
  DisplayingUpdateProductForm = "DisplayingUpdateProductForm",
  DisplayingDeleteProductForm = "DisplayingDeleteProductForm",
  UpdatingProduct = "UpdatingProduct",
  DeletingProduct = "DeletingProduct",
}

export enum AddProductState {
  Idle = "Idle",
  DisplayingForm = "DisplayingForm",
  AddingProduct = "AddingProduct",
  AddingProductFormRawData = "AddingProductFormRawData",
  AddingProductsFormRawData = "AddingProductsFormRawData",
}

const prodStateMap: Record<string, ProductState> = {
  idle: ProductState.Idle,
  "displayingProducts.fetchingProducts": ProductState.FetchingProducts,
  "displayingProducts.displayingProductsTable": ProductState.DisplayingProductsTable,

  "displayingProducts.displayingProductsDetailModal.displayingProduct": ProductState.DisplayingProductsDetailModal,
  "displayingProducts.displayingProductsDetailModal.displayingUpdateProductForm": ProductState.DisplayingProductsDetailModal,
  "displayingProducts.displayingProductsDetailModal.displayingDeleteProductForm": ProductState.DisplayingProductsDetailModal,
  "displayingProducts.displayingProductsDetailModal.displayingUpdateProductForm.updatingProduct": ProductState.DisplayingProductsDetailModal,
  "displayingProducts.displayingProductsDetailModal.displayingDeleteProductForm.deletingProduct": ProductState.DisplayingProductsDetailModal,

  "displayingProducts.displayingAddProductsForm.displayingForm": ProductState.DisplayingAddProductsForm,
};

const dispProdStateMap: Record<string, DisplayProductState> = {
  "displayingProducts.displayingProductsDetailModal.displayingProduct": DisplayProductState.DisplayingProduct,
  "displayingProducts.displayingProductsDetailModal.displayingUpdateProductForm": DisplayProductState.DisplayingUpdateProductForm,
  "displayingProducts.displayingProductsDetailModal.displayingDeleteProductForm": DisplayProductState.DisplayingDeleteProductForm,
  "displayingProducts.displayingProductsDetailModal.updatingProduct": DisplayProductState.UpdatingProduct,
  "displayingProducts.displayingProductsDetailModal.deletingProduct": DisplayProductState.DeletingProduct,
};

const addProdStateMap: Record<string, AddProductState> = {
  "displayingProducts.displayingAddProductsForm.displayingForm": AddProductState.DisplayingForm,
  "displayingProducts.displayingAddProductsForm.addingProduct": AddProductState.AddingProduct,
  "displayingProducts.displayingAddProductsForm.addingProductFormRawData": AddProductState.AddingProductFormRawData,
  "displayingProducts.displayingAddProductsForm.addingProductsFormRawData": AddProductState.AddingProductsFormRawData,
};

export const useProductContext = () => {
  const { actorRef } = useAppContext();
  const productActorRef = actorRef.product;
  const productActorState = useSelector(productActorRef, (state) => state);
  useToast(productActorRef);

  const productState = useMemo(() => {
    if (!productActorState) return ProductState.Idle;
    const currentState = convertStateToString(productActorState.value as any);
    return prodStateMap[currentState] || ProductState.Idle;
  }, [productActorState]);

  const displayProductState = useMemo(() => {
    const currentState = convertStateToString(productActorState.value as any);
    return dispProdStateMap[currentState] || DisplayProductState.Idle;
  }, [productActorState]);

  const addProductState = useMemo(() => {
    const currentState = convertStateToString(productActorState.value as any);
    return addProdStateMap[currentState] || AddProductState.Idle;
  }, [productActorState]);

  const productDispatch = useCallback(
    (action: Parameters<typeof productMachine.transition>[1]) => {
      productActorRef?.send(action);
    },
    [productActorRef]
  );

  return {
    state: {
      productState,
      displayProductState,
      addProductState,
    },
    data: {
      product: useSelector(productActorRef, (state) => state?.context.product || null),
      products: useSelector(productActorRef, (state) => state?.context.products || []),
      currentPage: useSelector(productActorRef, (state) => state?.context.currentPage || 0),
      totalProducts: useSelector(productActorRef, (state) => state?.context.totalProducts || 0),
      filter: useSelector(productActorRef, (state) => state?.context.filter),
    },
    actions: {
      click: {
        selectProduct: (product: Product) => productDispatch({ type: "user.selectProduct", product }),
        selectUpdateProduct: () => productDispatch({ type: "user.selectUpdateProduct" }),
        selectDeleteProduct: () => productDispatch({ type: "user.selectDeleteProduct" }),
        addProducts: () => productDispatch({ type: "user.addProducts" }),
        nextPage: () => productDispatch({ type: "user.nextPage" }),
        previousPage: () => productDispatch({ type: "user.previousPage" }),
      },
      submit: {
        deleteProduct: (id: string) => productDispatch({ type: "user.submitDeleteProduct", id }),
        updateProduct: (productData: Product) => productDispatch({ type: "user.submitUpdateProduct", productData }),
        addProduct: (productData: Product) => productDispatch({ type: "user.submitAddProduct", productData }),
        addProductRawData: (
          productId: string,
          rawData: string,
          maxMissingFeatureAttempts: number,
          maxLowConfidenceAttempts: number,
          maxNoProgressAttempts: number,
          confidenceThreshold: number
        ) =>
          productDispatch({
            type: "user.submitAddProductRawData",
            productId,
            rawData,
            maxMissingFeatureAttempts,
            maxLowConfidenceAttempts,
            maxNoProgressAttempts,
            confidenceThreshold,
          }),
        addProductsRawData: (
          file: File,
          maxMissingFeatureAttempts: number,
          maxLowConfidenceAttempts: number,
          maxNoProgressAttempts: number,
          confidenceThreshold: number,
          batchSize: number
        ) =>
          productDispatch({
            type: "user.submitAddProductsRawData",
            file,
            maxMissingFeatureAttempts,
            maxLowConfidenceAttempts,
            maxNoProgressAttempts,
            confidenceThreshold,
            batchSize,
          }),
        applyFilter: (filter: Record<string, string>) => productDispatch({ type: "user.applyFilter", filter }),
      },
      close: {
        productDetailModal: () => productDispatch({ type: "user.closeProductDetailModal" }),
        addProducts: () => productDispatch({ type: "user.closeAddProducts" }),
      },
      cancel: {
        productUpdate: () => productDispatch({ type: "user.cancelProductUpdate" }),
        addProduct: () => productDispatch({ type: "user.closeAddProducts" }),
      },
    },
  };
};

export type ProductData = ReturnType<typeof useProductContext>["data"];
export type ProductActions = ReturnType<typeof useProductContext>["actions"];
