import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { getScoreColor } from "@/lib/utils/scores";
import {
  AccuracyTestResult,
  ConsistencyTestResult,
  ContextRetentionTestResult,
  DefensibilityTestResult,
  FeatureInferenceTestResult,
  Product,
  ResponseMessage,
  RobustnessTestResult,
  TestCase,
} from "@/types";
import { DownloadIcon } from "lucide-react";
import React, { useMemo, useState } from "react";
import ResultModal from "../modals/ResultModal";

export type TransformedData = {
  messageId: string;
  sessionId: string;
  testType: string;
  input: string;
  model: string;
  architectureChoice: string;
  historyManagementChoice: string;
  responseType: string;
  response: string;
  products?: Product[];
  reasoning?: string;
  followUpQuestion?: string;
  metadata: Record<string, unknown>;
  // Metrics for different test types
  productAccuracy?: number;
  productConsistency?: number;
  orderConsistency?: number;
  filterAccuracy?: number;
  contextAccuracy?: number;
  noiseFiltering?: number;
  flowCoherence?: number;
  appropriateResponse?: boolean;
  error?: string;
  tags?: string[];
  timestamp: Date;
  // New fields for context retention
  filterProgression?: Array<Record<string, any>>;
  conversation?: ResponseMessage[];
  variationResponses?: {
    type: string;
    response: string;
    products?: Product[];
    reasoning?: string;
    followUpQuestion?: string;
    metadata: Record<string, unknown>;
  }[];
  description: string;
  extractedFilters?: Record<string, any>;
  // Fields for defensibility test
  boundaryMaintenance?: number;
  // Fields for conversational flow test
  topicTransitionAccuracy?: number;
};

const TestResultCard: React.FC = () => {
  const { data } = useTestRunnerContext();
  const [showModal, setShowingModal] = useState(false);
  const [selectedTestResult, setSelectedTestResult] = useState<TransformedData | null>(null);

  const transformedData: TransformedData[] = useMemo(() => {
    if (!data.testResults) return [];
    return data.testResults.map((testResult, index: number) => {
      const testCase = data.testCases![index];
      return transformTestResult(testResult, testCase);
    });
  }, [data.testResults, data.testCases]);

  const columns = useMemo(() => getColumns(), []);

  const allColumns = useMemo(() => getAllColumns(data.testCases?.[0]?.testType), [data.testCases]);

  const onSelectTestResult = (testResult: TransformedData) => {
    setSelectedTestResult(testResult);
    setShowingModal(true);
  };

  return (
    <div className="mt-8">
      <Card className="bg-card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-card-foreground">Test Results</h2>
          <Button variant="ghost" size="icon" onClick={() => downloadCSV(allColumns, transformedData)}>
            <DownloadIcon className="h-5 w-5 text-card-foreground" />
          </Button>
        </div>
        <div className="mt-4 overflow-auto">
          <SortableTable columns={columns} data={transformedData} onRowClick={onSelectTestResult} />
        </div>
      </Card>
      {selectedTestResult && (
        <ResultModal
          isOpen={showModal}
          onClose={() => setShowingModal(false)}
          data={selectedTestResult}
          testCase={data.testCases?.[transformedData.findIndex((d) => d.messageId === selectedTestResult.messageId)]}
        />
      )}
    </div>
  );
};

const transformTestResult = (testResult: any, testCase: TestCase): TransformedData => {
  const baseData = {
    testType: testCase.testType,
    input: testCase.prompt,
    description: testCase.description,
    tags: testCase.tags,
    timestamp: testResult.response?.timestamp ? new Date(testResult.response.timestamp) : new Date(),
  };

  switch (testCase.testType) {
    case "accuracy":
      const accuracyResult = testResult as AccuracyTestResult;
      return {
        ...baseData,
        messageId: accuracyResult.response.messageId,
        sessionId: accuracyResult.response.sessionId,
        model: accuracyResult.response.model,
        architectureChoice: accuracyResult.response.architectureChoice,
        historyManagementChoice: accuracyResult.response.historyManagementChoice,
        responseType: accuracyResult.response.message.type,
        response: accuracyResult.response.message.message,
        products: accuracyResult.response.message.products,
        reasoning: accuracyResult.response.message.reasoning,
        followUpQuestion: accuracyResult.response.message.followUpQuestion,
        metadata: accuracyResult.response.message.metadata,
        productAccuracy: accuracyResult.productAccuracy,
      };
    case "consistency":
      const consistencyResult = testResult as ConsistencyTestResult;
      return {
        ...baseData,
        messageId: consistencyResult.mainPromptResponse.messageId,
        sessionId: consistencyResult.mainPromptResponse.sessionId,
        model: consistencyResult.mainPromptResponse.model,
        architectureChoice: consistencyResult.mainPromptResponse.architectureChoice,
        historyManagementChoice: consistencyResult.mainPromptResponse.historyManagementChoice,
        responseType: consistencyResult.mainPromptResponse.message.type,
        response: consistencyResult.mainPromptResponse.message.message,
        products: consistencyResult.mainPromptResponse.message.products,
        reasoning: consistencyResult.mainPromptResponse.message.reasoning,
        followUpQuestion: consistencyResult.mainPromptResponse.message.followUpQuestion,
        metadata: consistencyResult.mainPromptResponse.message.metadata,
        productConsistency: consistencyResult.productConsistency,
        orderConsistency: consistencyResult.orderConsistency,
        variationResponses: consistencyResult.variationResponses.map((vr) => ({
          type: vr.message.type,
          response: vr.message.message,
          products: vr.message.products,
          reasoning: vr.message.reasoning,
          followUpQuestion: vr.message.followUpQuestion,
          metadata: vr.message.metadata,
        })),
      };
    case "feature_inference":
      const featureResult = testResult as FeatureInferenceTestResult;
      return {
        ...baseData,
        messageId: featureResult.response.messageId,
        sessionId: featureResult.response.sessionId,
        model: featureResult.response.model,
        architectureChoice: featureResult.response.architectureChoice,
        historyManagementChoice: featureResult.response.historyManagementChoice,
        responseType: featureResult.response.message.type,
        response: featureResult.response.message.message,
        reasoning: featureResult.response.message.reasoning,
        followUpQuestion: featureResult.response.message.followUpQuestion,
        metadata: featureResult.response.message.metadata,
        filterAccuracy: featureResult.filterAccuracy,
        extractedFilters: featureResult.extractedFilters,
        expectedFilters: featureResult.expectedFilters,
      };
    case "context_retention":
      const contextResult = testResult as ContextRetentionTestResult;
      return {
        ...baseData,
        messageId: contextResult.conversation[0].messageId,
        sessionId: contextResult.conversation[0].sessionId,
        model: contextResult.conversation[0].model,
        architectureChoice: contextResult.conversation[0].architectureChoice,
        historyManagementChoice: contextResult.conversation[0].historyManagementChoice,
        responseType: contextResult.conversation[0].message.type,
        response: contextResult.conversation[0].message.message,
        metadata: contextResult.conversation[0].message.metadata,
        contextAccuracy: contextResult.contextAccuracy,
        filterProgression: contextResult.filterProgression,
        conversation: contextResult.conversation,
      };
    case "conversational_flow":
      const flowResult = testResult as ConversationalFlowTestResult;
      return {
        ...baseData,
        messageId: flowResult.conversation[0].messageId,
        sessionId: flowResult.conversation[0].sessionId,
        model: flowResult.conversation[0].model,
        architectureChoice: flowResult.conversation[0].architectureChoice,
        historyManagementChoice: flowResult.conversation[0].historyManagementChoice,
        responseType: flowResult.conversation[0].message.type,
        response: flowResult.conversation[0].message.message,
        metadata: flowResult.conversation[0].message.metadata,
        flowCoherence: flowResult.flowCoherence,
        topicTransitionAccuracy: flowResult.topicTransitionAccuracy,
        conversation: flowResult.conversation,
      };
    case "defensibility":
      const defensibilityResult = testResult as DefensibilityTestResult;
      return {
        ...baseData,
        messageId: defensibilityResult.conversation[0].messageId,
        sessionId: defensibilityResult.conversation[0].sessionId,
        model: defensibilityResult.conversation[0].model,
        architectureChoice: defensibilityResult.conversation[0].architectureChoice,
        historyManagementChoice: defensibilityResult.conversation[0].historyManagementChoice,
        responseType: defensibilityResult.conversation[0].message.type,
        response: defensibilityResult.conversation[0].message.message,
        metadata: defensibilityResult.conversation[0].message.metadata,
        boundaryMaintenance: defensibilityResult.boundaryMaintenance,
        appropriateResponse: defensibilityResult.appropriateResponse,
        conversation: defensibilityResult.conversation,
      };
    case "robustness":
      const robustnessResult = testResult as RobustnessTestResult;
      return {
        ...baseData,
        messageId: robustnessResult.response.messageId,
        sessionId: robustnessResult.response.sessionId,
        model: robustnessResult.response.model,
        architectureChoice: robustnessResult.response.architectureChoice,
        historyManagementChoice: robustnessResult.response.historyManagementChoice,
        responseType: robustnessResult.response.message.type,
        response: robustnessResult.response.message.message,
        metadata: robustnessResult.response.message.metadata || {},
        filterAccuracy: robustnessResult.filterAccuracy,
        noiseFiltering: robustnessResult.noiseFiltering,
        extractedFilters: robustnessResult.extractedFilters,
      };
    default:
      return baseData as TransformedData;
  }
};

const getColumns = (): TableColumn[] => {
  const baseColumns: TableColumn[] = [
    {
      header: "Description",
      accessor: "description",
      sortable: true,
      cell: (value: string) => (
        <div className="max-w-md truncate" title={value}>
          {value}
        </div>
      ),
    },
    { header: "Test Type", accessor: "testType", sortable: true },
    { header: "Model", accessor: "model", sortable: true },
    { header: "Architecture", accessor: "architectureChoice", sortable: true },
    {
      header: "Timestamp",
      accessor: "timestamp",
      sortable: true,
      cell: (value: Date) => value.toLocaleString(),
    },
  ];

  const scoreColumns: TableColumn[] = [
    {
      header: "Product Accuracy",
      accessor: "productAccuracy",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "accuracy",
    },
    {
      header: "Product Consistency",
      accessor: "productConsistency",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "consistency",
    },
    {
      header: "Order Consistency",
      accessor: "orderConsistency",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "consistency",
    },
    {
      header: "Filter Accuracy",
      accessor: "filterAccuracy",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "feature_inference" || row.testType === "robustness",
    },
    {
      header: "Context Accuracy",
      accessor: "contextAccuracy",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "context_retention",
    },
    {
      header: "Noise Filtering",
      accessor: "noiseFiltering",
      sortable: true,
      cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      showIf: (row: TransformedData) => row.testType === "robustness",
    },
    {
      header: "Boundary Maintenance",
      accessor: "boundaryMaintenance",
      sortable: true,
      cell: (value: number | undefined) => (
        <div className={`font-medium ${getScoreColor(value)}`}>
          {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
        </div>
      ),
      showIf: (row: TransformedData) => row.testType === "defensibility",
    },
    {
      header: "Appropriate Response",
      accessor: "appropriateResponse",
      sortable: true,
      cell: (value: boolean | undefined) => (
        <div className={`font-medium ${value ? "text-green-600" : "text-red-600"}`}>
          {value !== undefined ? (value ? "Yes" : "No") : "-"}
        </div>
      ),
      showIf: (row: TransformedData) => row.testType === "defensibility",
    },
    {
      header: "Flow Coherence",
      accessor: "flowCoherence",
      sortable: true,
      cell: (value: number | undefined) => (
        <div className={`font-medium ${getScoreColor(value)}`}>
          {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
        </div>
      ),
      showIf: (row: TransformedData) => row.testType === "conversational_flow",
    },
    {
      header: "Topic Transition",
      accessor: "topicTransitionAccuracy",
      sortable: true,
      cell: (value: number | undefined) => (
        <div className={`font-medium ${getScoreColor(value)}`}>
          {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
        </div>
      ),
      showIf: (row: TransformedData) => row.testType === "conversational_flow",
    },
  ];

  return [...baseColumns, ...scoreColumns];
};

const getAllColumns = (testType: string | undefined): TableColumn[] => {
  const baseColumns = getColumns();

  switch (testType) {
    case "accuracy":
      baseColumns.push({
        header: "Product Accuracy",
        accessor: "productAccuracy",
        sortable: true,
        cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
      });
      break;

    case "consistency":
      baseColumns.push(
        {
          header: "Product Consistency",
          accessor: "productConsistency",
          sortable: true,
          cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
        },
        {
          header: "Order Consistency",
          accessor: "orderConsistency",
          sortable: true,
          cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
        }
      );
      break;

    case "feature_inference":
      baseColumns.push(
        {
          header: "Filter Accuracy",
          accessor: "filterAccuracy",
          sortable: true,
          cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
        },
        {
          header: "Extracted Filters",
          accessor: "extractedFilters",
          cell: (value: Record<string, any> | undefined) => <pre className="max-w-xs truncate">{value ? JSON.stringify(value, null, 2) : "-"}</pre>,
        },
        {
          header: "Expected Filters",
          accessor: "expectedFilters",
          cell: (value: Record<string, any> | undefined) => <pre className="max-w-xs truncate">{value ? JSON.stringify(value, null, 2) : "-"}</pre>,
        }
      );
      break;

    case "context_retention":
      baseColumns.push(
        {
          header: "Context Accuracy",
          accessor: "contextAccuracy",
          sortable: true,
          cell: (value: number | undefined) => <div className={`font-medium ${getScoreColor(value)}`}>{value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}</div>,
        },
        {
          header: "Conversation Turns",
          accessor: "conversation",
          cell: (value: ResponseMessage[] | undefined) => (value ? value.length : "-"),
        },
        {
          header: "Filter Progression",
          accessor: "filterProgression",
          cell: (value: Array<Record<string, any>> | undefined) => (
            <div className="max-w-xs truncate">{value ? value.map((filters, i) => `Turn ${i + 1}: ${Object.keys(filters).length} filters`).join(", ") : "-"}</div>
          ),
        }
      );
      break;

    case "conversational_flow":
      baseColumns.push(
        {
          header: "Flow Coherence",
          accessor: "flowCoherence",
          sortable: true,
          cell: (value: number | undefined) => (
            <div className={`font-medium ${getScoreColor(value)}`}>
              {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
            </div>
          ),
        },
        {
          header: "Topic Transition",
          accessor: "topicTransitionAccuracy",
          sortable: true,
          cell: (value: number | undefined) => (
            <div className={`font-medium ${getScoreColor(value)}`}>
              {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
            </div>
          ),
        }
      );
      break;

    case "defensibility":
      baseColumns.push(
        {
          header: "Boundary Maintenance",
          accessor: "boundaryMaintenance",
          sortable: true,
          cell: (value: number | undefined) => (
            <div className={`font-medium ${getScoreColor(value)}`}>
              {value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"}
            </div>
          ),
        },
        {
          header: "Appropriate Response",
          accessor: "appropriateResponse",
          sortable: true,
          cell: (value: boolean | undefined) => (
            <div className={`font-medium ${value ? "text-green-600" : "text-red-600"}`}>
              {value !== undefined ? (value ? "Yes" : "No") : "-"}
            </div>
          ),
        }
      );
      break;
  }

  return baseColumns;
};

const downloadCSV = (columns: TableColumn[], data: TransformedData[]) => {
  // Create header row
  const headers = columns.map((col) => `"${col.header}"`).join(",");
  const csvRows = [headers];

  // Process each row
  data.forEach((row) => {
    const rowData = columns
      .map((col) => {
        let cellData: any = row[col.accessor as keyof TransformedData];

        // Format the data based on type
        if (cellData === undefined || cellData === null) {
          return '""';
        }

        // Handle different data types
        if (col.accessor === "timestamp" && cellData instanceof Date) {
          return `"${cellData.toLocaleString()}"`;
        }

        // Handle numeric metrics
        if (["productAccuracy", "productConsistency", "orderConsistency", "filterAccuracy", "contextAccuracy", "noiseFiltering", "flowCoherence"].includes(col.accessor)) {
          return cellData !== undefined ? `"${(cellData * 100).toFixed(2)}%"` : '""';
        }

        // Handle objects and arrays
        if (typeof cellData === "object") {
          if (Array.isArray(cellData)) {
            return `"${cellData.join("; ")}"`;
          }
          // Convert object to string representation
          return `"${JSON.stringify(cellData).replace(/"/g, '""')}"`;
        }

        // Handle basic strings and numbers
        return `"${String(cellData).replace(/"/g, '""')}"`;
      })
      .join(",");

    csvRows.push(rowData);

    // Handle special cases for different test types
    if (row.testType === "consistency" && row.variationResponses) {
      row.variationResponses.forEach((variation, index) => {
        const variationRow = columns
          .map((col) => {
            switch (col.accessor) {
              case "messageId":
                return `"${row.messageId}_variation_${index + 1}"`;
              case "response":
                return `"${variation.response.replace(/"/g, '""')}"`;
              case "products":
                return `"${JSON.stringify(variation.products).replace(/"/g, '""')}"`;
              case "reasoning":
                return `"${(variation.reasoning || "").replace(/"/g, '""')}"`;
              case "metadata":
                return `"${JSON.stringify(variation.metadata).replace(/"/g, '""')}"`;
              default:
                return `"${String(row[col.accessor as keyof TransformedData] || "").replace(/"/g, '""')}"`;
            }
          })
          .join(",");
        csvRows.push(variationRow);
      });
    }

    // Handle context retention conversation turns
    if (row.testType === "context_retention" && row.conversation) {
      row.conversation.forEach((turn, index) => {
        const turnRow = columns
          .map((col) => {
            switch (col.accessor) {
              case "messageId":
                return `"${row.messageId}_turn_${index + 1}"`;
              case "response":
                return `"${turn.message.message.replace(/"/g, '""')}"`;
              case "metadata":
                return `"${JSON.stringify(turn.message.metadata).replace(/"/g, '""')}"`;
              case "filterProgression":
                return `"${JSON.stringify(row.filterProgression?.[index] || {}).replace(/"/g, '""')}"`;
              default:
                return `"${String(row[col.accessor as keyof TransformedData] || "").replace(/"/g, '""')}"`;
            }
          })
          .join(",");
        csvRows.push(turnRow);
      });
    }
  });

  // Create and download the CSV file
  const csvContent = csvRows.join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "test_results.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url); // Clean up
  }
};

export default TestResultCard;
