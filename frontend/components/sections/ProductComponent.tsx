"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProductState, useProductContext } from "@/hooks/useProductContext";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import SortableTable, { TableColumn } from "../blocks/SortableTable";
import AddProduct from "./AddProduct";
import ProductDetail from "./ProductDetail";

const filterableFeatures = [
  { value: "name", label: "Name" },
  { value: "manufacturer", label: "Manufacturer" },
  { value: "form_factor", label: "Form Factor" },
  { value: "processor", label: "Processor" },
  { value: "operating_system", label: "Operating System" },
];

const ProductComponent = () => {
  const { state, data, actions } = useProductContext();
  const [filterFeature, setFilterFeature] = useState("");
  const [filterValue, setFilterValue] = useState("");

  const columns: TableColumn[] = [
    { header: "Name", accessor: "name", sortable: true },
    { header: "Manufacturer", accessor: "manufacturer", sortable: true },
    { header: "Form", accessor: "formFactor", sortable: true },
    { header: "Processor", accessor: "processor", sortable: true },
    { header: "Core Count", accessor: "coreCount", sortable: true },
    { header: "Memory", accessor: "memory", sortable: true },
    { header: "OS", accessor: "operatingSystem", sortable: true },
  ];

  const handleFilterFeatureChange = (value: string) => {
    setFilterFeature(value);
    setFilterValue(""); // Reset filter value when feature changes
  };

  const handleFilterValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterValue(e.target.value);
  };

  const applyFilter = () => {
    if (filterFeature && filterValue) {
      actions.submit.applyFilter({ [filterFeature]: filterValue });
    }
  };

  const clearFilter = () => {
    setFilterFeature("");
    setFilterValue("");
    actions.submit.applyFilter({});
  };

  const renderProductList = () => (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Product Management</h1>
        <Button size="sm" onClick={actions.click.addProducts}>
          Add New Product
        </Button>
      </div>
      <div className="mb-4 flex items-end space-x-2">
        <div className="w-1/3">
          <Select value={filterFeature} onValueChange={handleFilterFeatureChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select feature to filter" />
            </SelectTrigger>
            <SelectContent>
              {filterableFeatures.map((feature) => (
                <SelectItem key={feature.value} value={feature.value}>
                  {feature.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-1/3">
          <Input type="text" placeholder="Filter value..." value={filterValue} onChange={handleFilterValueChange} disabled={!filterFeature} />
        </div>
        <Button onClick={applyFilter} disabled={!filterFeature || !filterValue}>
          Apply Filter
        </Button>
        <Button variant="outline" onClick={clearFilter}>
          Clear Filter
        </Button>
      </div>
      <div className="overflow-hidden rounded-lg bg-white shadow-md">
        <SortableTable columns={columns} data={data.products} onRowClick={actions.click.selectProduct} />
      </div>
      <div className="mt-4 flex justify-between">
        <Button onClick={actions.click.previousPage} disabled={data.currentPage === 0}>
          Previous
        </Button>
        <span>
          Page {data.currentPage + 1} of {Math.ceil(data.totalProducts / 20)}
        </span>
        <Button onClick={actions.click.nextPage} disabled={(data.currentPage + 1) * 20 >= data.totalProducts}>
          Next
        </Button>
      </div>
    </div>
  );

  const render = () => {
    switch (state.productState) {
      case ProductState.Idle:
      case ProductState.FetchingProducts:
        return (
          <div className="flex h-screen items-center justify-center">
            <Loader2 className="mr-2 h-16 w-16 animate-spin" />
          </div>
        );
      case ProductState.DisplayingProductsTable:
        return renderProductList();
      case ProductState.DisplayingAddProductsForm:
        return <AddProduct state={state.addProductState} actions={actions} />;
      case ProductState.DisplayingProductsDetailModal:
        return <ProductDetail state={state.displayProductState} product={data.product} actions={actions} />;
      default:
        return null;
    }
  };

  return render();
};

export default ProductComponent;
