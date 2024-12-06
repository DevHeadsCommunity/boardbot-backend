import { Product } from "@/types";
import React, { memo } from "react";

interface ProductListProps {
  products: Product[];
  onProductSelect: (product: Product) => void;
}

const ProductList: React.FC<ProductListProps> = memo(function ProductList({ products, onProductSelect }) {
  return (
    <ul className="mb-2 list-disc pl-5">
      {products.map((product) => (
        <li key={product.id} className="cursor-pointer text-blue-600 hover:underline" onClick={() => onProductSelect(product)}>
          {product.name}
        </li>
      ))}
    </ul>
  );
});

const ProductDetails: React.FC<{ product: Product }> = memo(function ProductDetails({ product }) {
  return (
    <div className="w-full max-w-md rounded-lg bg-white shadow-md">
      <div className="max-h-[80vh] overflow-y-auto p-6">
        <h3 className="mb-4 text-xl font-bold text-blue-600">{product.name}</h3>

        <div className="mb-4 grid grid-cols-1 gap-4">
          <InfoItem label="ID" value={product.id || "N/A"} />
          <InfoItem label="Product ID" value={product.productId} />
          <InfoItem label="Manufacturer" value={product.manufacturer} />
          <InfoItem label="Form Factor" value={product.formFactor} />
        </div>

        <Section title="Processor Details">
          <InfoItem label="Architecture" value={product.processorArchitecture} />
          <InfoItem label="Core Count" value={product.processorCoreCount} />
          <InfoItem label="Manufacturer" value={product.processorManufacturer} />
          <InfoItem label="TDP" value={product.processorTdp} />
        </Section>

        <Section title="Memory and Storage">
          <InfoItem label="Memory" value={product.memory} />
          <InfoItem label="Onboard Storage" value={product.onboardStorage} />
        </Section>

        <Section title="Connectivity">
          <InfoItem label="I/O Count" value={product.ioCount?.join(", ")} />
          <InfoItem label="Wireless" value={product.wireless?.join(", ")} />
          <InfoItem label="Input Voltage" value={product.inputVoltage} />
        </Section>

        <Section title="Software and Environment">
          <InfoItem label="OS/BSP" value={product.operatingSystemBsp?.join(", ")} />
          <InfoItem
            label="Operating Temp"
            value={product.operatingTemperatureMin && product.operatingTemperatureMax ? `${product.operatingTemperatureMin} to ${product.operatingTemperatureMax}` : undefined}
          />
        </Section>

        <Section title="Additional Information">
          <InfoItem label="Eval/Commercialization" value={product.evaluationOrCommercialization} />
          <InfoItem label="Certifications" value={product.certifications?.join(", ")} />
        </Section>

        <Section title="Availability">
          <InfoItem label="Price" value={product.price} />
          <InfoItem label="Stock" value={product.stockAvailability} />
        </Section>
      </div>
    </div>
  );
});

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="mb-4 border-t border-gray-200 pt-4">
    <h4 className="mb-2 font-semibold text-gray-700">{title}</h4>
    <div className="grid grid-cols-1 gap-2">{children}</div>
  </div>
);

const InfoItem: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => {
  if (!value) return null;
  return (
    <div className="break-words">
      <span className="text-sm font-medium text-gray-500">{label}:</span>
      <p className="text-sm text-gray-900">{value}</p>
    </div>
  );
};

export default ProductList;
