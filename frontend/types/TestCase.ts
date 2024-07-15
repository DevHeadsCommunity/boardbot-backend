import { Product } from "./Product";

export interface TestCase {
  id: string;
  input: string;
  expectedProducts: Product[];
  metadata?: Record<string, unknown>;
  tags?: string[];
}
