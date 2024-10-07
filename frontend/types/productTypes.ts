import { transformKeys } from "@/lib/caseConversion";
import { z } from "zod";

export const ProductSchema = z.object({
  id: z.string().optional().nullable(),
  productId: z.string(),
  duplicateIds: z.array(z.string()).optional().nullable(),
  name: z.string(),
  manufacturer: z.string(),
  formFactor: z.string(),
  evaluationOrCommercialization: z.string().optional().nullable(),
  processorArchitecture: z.string().optional().nullable(),
  processorCoreCount: z.string().optional().nullable(),
  processorManufacturer: z.string().optional().nullable(),
  processorTdp: z.string().optional().nullable(),
  memory: z.string().optional().nullable(),
  onboardStorage: z.string().optional().nullable(),
  inputVoltage: z.string().optional().nullable(),
  ioCount: z.array(z.string()).optional().nullable(),
  wireless: z.array(z.string()).optional().nullable(),
  operatingSystemBsp: z.array(z.string()).optional().nullable(),
  operatingTemperatureMax: z.string().optional().nullable(),
  operatingTemperatureMin: z.string().optional().nullable(),
  certifications: z.array(z.string()).optional().nullable(),
  price: z.string().optional().nullable(),
  stockAvailability: z.string().optional().nullable(),
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
