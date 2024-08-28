"use client";

import { Button } from "@/components/ui/button";
import { ProductState, useProductContext } from "@/hooks/useProductContext";
import { Loader2 } from "lucide-react";
import SortableTable, { TableColumn } from "../blocks/SortableTable";
import AddProduct from "./AddProduct";
import ProductDetail from "./ProductDetail";

const ProductComponent = () => {
  const { state, data, actions } = useProductContext();
  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Manufacturer", accessor: "manufacturer" },
    { header: "Form", accessor: "formFactor" },
    { header: "Processor", accessor: "processor" },
    { header: "Core Count", accessor: "coreCount" },
    { header: "Memory", accessor: "memory" },
    { header: "OS", accessor: "operatingSystem" },
  ];

  console.log("ProductComponent state:", state);
  console.log("ProductComponent data:", data);

  const render = () => {
    switch (state.productState) {
      case ProductState.Idle:
        return null;
      case ProductState.FetchingProducts:
        return (
          <div className="flex h-screen items-center justify-center">
            <Loader2 className="mr-2 h-16 w-16 animate-spin" />
          </div>
        );
      case ProductState.DisplayingProducts:
        return (
          <div className="container mx-auto px-4 py-8">
            <div className="mb-6 flex items-center justify-between">
              <h1 className="text-2xl font-bold">Product Management</h1>
              <Button size="sm" onClick={actions.click.addProducts}>
                Add New Product
              </Button>
            </div>
            <div className="overflow-hidden rounded-lg bg-white shadow-md">
              <SortableTable columns={columns} data={data.products} onRowClick={actions.click.selectProduct} />
            </div>
          </div>
        );
      case ProductState.AddingProduct:
        return <AddProduct state={state.addProductState} actions={actions} />;
      case ProductState.DisplayingProduct:
        return <ProductDetail state={state.displayProductState} product={data.product} actions={actions} />;
      default:
        return null;
    }
  };

  return render();
};

export default ProductComponent;
