export interface FullTestResult {
  averageInputTokenCount: number;
  averageOutputTokenCount: number;
  averageLlmResponseTime: number;
  averageBackendProcessingTime: number;
  averageTotalResponseTime: number;
  averageProductAccuracy: number;
  averageFeatureAccuracy: number;
  error?: string;
  metadata?: Record<string, unknown>;
}
