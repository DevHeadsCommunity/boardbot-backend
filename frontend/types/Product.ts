export interface Product {
  id: string;
  name: string;
  ids: string;
  manufacturer: string;
  formFactor: string;
  processor: string;
  coreCount: string;
  processorTdp: string;
  memory: string;
  io: string;
  operatingSystem: string;
  environmentals: string;
  certifications: string;
  shortSummary: string;
  fullSummary: string;
  fullProductDescription: string;
}

export const ProductFromJson = (productJson: any): Product => {
  try {
    return {
      id: productJson._additional.id || "", // Assuming there's an id field, if not, you might need to generate one
      name: productJson.name,
      ids: productJson.ids,
      manufacturer: productJson.manufacturer || "",
      formFactor: productJson.form_factor || "",
      processor: productJson.processor || "",
      coreCount: productJson.core_count || "",
      processorTdp: productJson.processor_tdp || "",
      memory: productJson.memory || "",
      io: productJson.io || "",
      operatingSystem: productJson.operating_system || "",
      environmentals: productJson.environmentals || "",
      certifications: productJson.certifications || "",
      shortSummary: productJson.short_summary || "",
      fullSummary: productJson.full_summary || "",
      fullProductDescription: productJson.full_product_description || "",
    } as Product;
  } catch (error) {
    console.error("Error parsing product:", error);
    throw error;
  }
};

export const ProductToJson = (product: Product): any => {
  return {
    id: product.id,
    name: product.name,
    ids: product.ids,
    manufacturer: product.manufacturer,
    form_factor: product.formFactor,
    processor: product.processor,
    core_count: product.coreCount,
    processor_tdp: product.processorTdp,
    memory: product.memory,
    io: product.io,
    operating_system: product.operatingSystem,
    environmentals: product.environmentals,
    certifications: product.certifications,
    short_summary: product.shortSummary,
    full_summary: product.fullSummary,
    full_product_description: product.fullProductDescription,
  };
};
