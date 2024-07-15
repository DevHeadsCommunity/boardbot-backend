export interface TestCase {
  id: string;
  input: string;
  expectedOutput: string;
  metadata?: Record<string, unknown>;
  tags?: string[];
}
