import { convertStateToString } from "@/lib/stateToStr";
import { FeatureExtractorType } from "@/machines/productMachine";
import { Product } from "@/types";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useAppContext } from "./useAppContext";

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
  "displayingProducts.displayingProductsDetailModal.displayingUpdateProductForm.updatingProduct": DisplayProductState.UpdatingProduct,
  "displayingProducts.displayingProductsDetailModal.displayingDeleteProductForm.deletingProduct": DisplayProductState.DeletingProduct,
};

const addProdStateMap: Record<string, AddProductState> = {
  "displayingProducts.displayingAddProductsForm.displayingForm": AddProductState.DisplayingForm,
  "displayingProducts.displayingAddProductsForm.addingProduct": AddProductState.AddingProduct,
  "displayingProducts.displayingAddProductsForm.addingProductFormRawData": AddProductState.AddingProductFormRawData,
  "displayingProducts.displayingAddProductsForm.addingProductsFormRawData": AddProductState.AddingProductsFormRawData,
};

type ProductAction =
  | { type: "user.selectProduct"; product: Product }
  | { type: "user.selectUpdateProduct" }
  | { type: "user.selectDeleteProduct" }
  | { type: "user.submitDeleteProduct"; productId: string }
  | { type: "user.submitUpdateProduct"; productData: Product }
  | { type: "user.cancelProductUpdate" }
  | { type: "user.closeProductDetailModal" }
  | { type: "user.addProducts" }
  | { type: "user.submitAddProduct"; productData: Product }
  | { type: "user.submitAddProductRawData"; productId: string; rawData: string; extractorType: FeatureExtractorType }
  | { type: "user.submitAddProductsRawData"; file: File; extractorType: FeatureExtractorType }
  | { type: "user.cancelAddProduct" }
  | { type: "user.closeAddProducts" }
  | { type: "user.nextPage" }
  | { type: "user.previousPage" }
  | { type: "user.applyFilter"; filter: Record<string, string> };

export const useProductContext = () => {
  const { actorRef } = useAppContext();
  const productActorRef = actorRef.product;
  const productActorState = useSelector(productActorRef, (state) => state);

  console.log(`productActorState: ${JSON.stringify(productActorState.value)}`);
  const productState = useMemo(() => {
    if (!productActorState) return ProductState.Idle;
    const currentState = convertStateToString(productActorState.value as any);
    console.log(`currentState: ${currentState}`);
    return prodStateMap[currentState] || ProductState.Idle;
  }, [productActorState]);

  const displayProductState = useMemo(() => {
    // if (productState !== ProductState.DisplayingProductsDetailModal) return DisplayProductState.Idle;
    const currentState = convertStateToString(productActorState.value as any);
    return dispProdStateMap[currentState] || DisplayProductState.Idle;
  }, [productActorState, productState]);

  const addProductState = useMemo(() => {
    // if (productState !== ProductState.DisplayingAddProductsForm) return AddProductState.Idle;
    const currentState = convertStateToString(productActorState.value as any);
    return addProdStateMap[currentState] || AddProductState.Idle;
  }, [productActorState, productState]);

  const productDispatch = useCallback(
    (action: ProductAction) => {
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
        deleteProduct: (productId: string) => productDispatch({ type: "user.submitDeleteProduct", productId }),
        updateProduct: (productData: Product) => productDispatch({ type: "user.submitUpdateProduct", productData }),
        addProduct: (productData: Product) => productDispatch({ type: "user.submitAddProduct", productData }),
        addProductRawData: (productId: string, rawData: string, extractorType: FeatureExtractorType) =>
          productDispatch({ type: "user.submitAddProductRawData", productId, rawData, extractorType }),
        addProductsRawData: (file: File, extractorType: FeatureExtractorType) => productDispatch({ type: "user.submitAddProductsRawData", file, extractorType }),
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
