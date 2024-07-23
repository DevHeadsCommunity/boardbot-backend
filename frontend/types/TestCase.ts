import { Product } from "./Product";

export interface TestCase {
  messageId: string;
  input: string;
  expectedProducts: Product[];
  metadata?: Record<string, unknown>;
  tags?: string[];
}
