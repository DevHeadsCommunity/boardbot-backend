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

export type Product = z.infer<typeof ProductSchema>;

export const productFromJson = (productJson: unknown): Product => {
  const camelCaseData = transformKeys(productJson as Record<string, any>, "snakeToCamel");
  return ProductSchema.parse(camelCaseData);
};

export const productToJson = (product: Product): unknown => {
  return transformKeys(product, "camelToSnake");
};
