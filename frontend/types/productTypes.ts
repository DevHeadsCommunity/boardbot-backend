import { transformKeys } from "@/lib/caseConversion";
import { z } from "zod";

export const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  ids: z.string(),
  manufacturer: z.string(),
  formFactor: z.string(),
  processor: z.string(),
  coreCount: z.string(),
  processorTdp: z.string(),
  memory: z.string(),
  io: z.string(),
  operatingSystem: z.string(),
  environmentals: z.string(),
  certifications: z.string(),
  shortSummary: z.string(),
  fullSummary: z.string(),
  fullProductDescription: z.string(),
});

export const ExpectedProductSchema = ProductSchema.partial().required({ name: true });
export const AddProductSchema = ProductSchema.omit({ id: true });

export type Product = z.infer<typeof ProductSchema>;

export const productFromJson = (productJson: unknown): Product => {
  try {
    const camelCaseData = transformKeys(productJson as Record<string, any>, "snakeToCamel");
    return ProductSchema.parse(camelCaseData);
  } catch (e) {
    console.error("Error parsing product from JSON:", e);
    if (e instanceof z.ZodError) {
      console.error("Zod validation errors:", JSON.stringify(e.errors, null, 2));
    }
    throw new Error("Invalid product data");
  }
};

export const productToJson = (product: Product): unknown => {
  return transformKeys(product, "camelToSnake");
};
