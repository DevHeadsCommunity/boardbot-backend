import { Product } from "@/types";
import React, { memo } from "react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";

interface ProductListProps {
  products: Product[];
}

const ProductList: React.FC<ProductListProps> = memo(function ProductList({ products }) {
  return (
    <ul className="mb-2 list-disc pl-5">
      {products.map((product) => (
        <li key={product.id} className="mb-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger className="cursor-pointer text-blue-600 hover:underline">{product.name}</TooltipTrigger>
              <TooltipContent>
                <ProductDetails product={product} />
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </li>
      ))}
    </ul>
  );
});

const ProductDetails: React.FC<{ product: Product }> = memo(function ProductDetails({ product }) {
  return (
    <div className="max-w-md">
      <h3 className="font-bold">{product.name}</h3>
      <p>
        <strong>ID:</strong> {product.id}
      </p>
      <p>
        <strong>Manufacturer:</strong> {product.manufacturer}
      </p>
      <p>
        <strong>Form Factor:</strong> {product.formFactor}
      </p>
      <p>
        <strong>Processor:</strong> {product.processor}
      </p>
      <p>
        <strong>Core Count:</strong> {product.coreCount}
      </p>
      <p>
        <strong>Memory:</strong> {product.memory}
      </p>
      <p>
        <strong>I/O:</strong> {product.io}
      </p>
    </div>
  );
});

export default ProductList;
