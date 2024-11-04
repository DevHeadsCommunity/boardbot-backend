import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { AccuracyTestResult, ConsistencyTestResult, Product, TestCase } from "@/types";
import { DownloadIcon } from "lucide-react";
import React, { useMemo, useState } from "react";
import ResultModal from "../modals/ResultModal";

export type TransformedData = {
  messageId: string;
  sessionId: string;
  testType: "accuracy" | "consistency";
  input: string;
  model: string;
  architectureChoice: string;
  historyManagementChoice: string;
  responseType: string;
  response: string;
  products: Product[];
  reasoning: string;
  followUpQuestion: string;
  metadata: Record<string, unknown>;
  productAccuracy?: number;
  featureAccuracy?: number;
  productConsistency?: number;
  orderConsistency?: number;
  error?: string;
  tags?: string[];
  timestamp: Date;
  variationResponses?: {
    type: string;
    response: string;
    products: Product[];
    reasoning: string;
    followUpQuestion: string;
    metadata: Record<string, unknown>;
  }[];
};

const TestResultCard: React.FC = () => {
  const { data } = useTestRunnerContext();
  const [showModal, setShowingModal] = useState(false);
  const [selectedTestResult, setSelectedTestResult] = useState<TransformedData | null>(null);

  const transformedData: TransformedData[] = useMemo(() => {
    if (!data.testResults) return [];
    return data.testResults.map((testResult: AccuracyTestResult | ConsistencyTestResult, index: number) => {
      const testCase = data.testCases![index];
      return transformTestResult(testResult, testCase);
    });
  }, [data.testResults, data.testCases]);

  const columns = useMemo(() => getColumns(), [transformedData]);

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

const transformTestResult = (testResult: AccuracyTestResult | ConsistencyTestResult, testCase: TestCase): TransformedData => {
  const baseData = {
    testType: testCase.testType,
    input: testCase.prompt,
    tags: testCase.tags,
  };

  if (testCase.testType === "accuracy") {
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
      featureAccuracy: accuracyResult.featureAccuracy,
      timestamp: accuracyResult.response.timestamp || new Date(),
    };
  } else {
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
      timestamp: consistencyResult.mainPromptResponse.timestamp || new Date(),
      variationResponses: consistencyResult.variationResponses.map((vr) => ({
        type: vr.message.type,
        response: vr.message.message,
        products: vr.message.products,
        reasoning: vr.message.reasoning,
        followUpQuestion: vr.message.followUpQuestion,
        metadata: vr.message.metadata,
      })),
    };
  }
};

const getColumns = (): TableColumn[] => {
  const baseColumns: TableColumn[] = [
    { header: "Message ID", accessor: "messageId", sortable: true },
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
      cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
      showIf: (row: TransformedData) => row.testType === "accuracy",
    },
    {
      header: "Product Consistency",
      accessor: "productConsistency",
      sortable: true,
      cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
      showIf: (row: TransformedData) => row.testType === "consistency",
    },
    {
      header: "Order Consistency",
      accessor: "orderConsistency",
      sortable: true,
      cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
      showIf: (row: TransformedData) => row.testType === "consistency",
    },
  ];

  return [...baseColumns, ...scoreColumns];
};

const getAllColumns = (testType?: "accuracy" | "consistency"): TableColumn[] => {
  const baseColumns = [
    ...getColumns(),
    { header: "Session ID", accessor: "sessionId", sortable: true },
    { header: "Input", accessor: "input", sortable: true },
    { header: "History Management", accessor: "historyManagementChoice", sortable: true },
    { header: "Response Type", accessor: "responseType", sortable: true },
    { header: "Response", accessor: "response", sortable: true },
    {
      header: "Products",
      accessor: "products",
      cell: (value: Product[]) =>
        JSON.stringify(
          value.map((product) => ({
            productId: product.productId,
            name: product.name,
            manufacturer: product.manufacturer,
            formFactor: product.formFactor,
            // Add new fields
            evaluationOrCommercialization: product.evaluationOrCommercialization,
            processorArchitecture: product.processorArchitecture,
            processorCoreCount: product.processorCoreCount,
            processorManufacturer: product.processorManufacturer,
            processorTdp: product.processorTdp,
            memory: product.memory,
            onboardStorage: product.onboardStorage,
            inputVoltage: product.inputVoltage,
            ioCount: product.ioCount,
            wireless: product.wireless,
            operatingSystemBsp: product.operatingSystemBsp,
            operatingTemperatureMax: product.operatingTemperatureMax,
            operatingTemperatureMin: product.operatingTemperatureMin,
            certifications: product.certifications,
            price: product.price,
            stockAvailability: product.stockAvailability,
          }))
        ),
    },
    { header: "Reasoning", accessor: "reasoning", sortable: true },
    { header: "Follow-up Question", accessor: "followUpQuestion", sortable: true },
    {
      header: "Metadata",
      accessor: "metadata",
      cell: (value: Record<string, unknown>) => JSON.stringify(value),
    },
    {
      header: "Tags",
      accessor: "tags",
      cell: (value: string[] | undefined) => (value ? value.join(", ") : ""),
    },
  ];

  // Add score columns based on test type
  if (testType === "accuracy") {
    baseColumns.push({
      header: "Product Accuracy",
      accessor: "productAccuracy",
      sortable: true,
      cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
    });
  } else if (testType === "consistency") {
    baseColumns.push(
      {
        header: "Product Consistency",
        accessor: "productConsistency",
        sortable: true,
        cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
      },
      {
        header: "Order Consistency",
        accessor: "orderConsistency",
        sortable: true,
        cell: (value: number | undefined) => (value !== undefined ? `${(value * 100).toFixed(2)}%` : "-"),
      }
    );
  }

  return baseColumns;
};

const downloadCSV = (columns: TableColumn[], data: TransformedData[]) => {
  const csvRows: string[] = [];
  const headers = columns.map((col) => col.header);
  csvRows.push(headers.join(","));

  data.forEach((row) => {
    // Add main prompt response
    csvRows.push(
      columns
        .map((col) => {
          let cellData = row[col.accessor as keyof TransformedData];
          if (col.cell) {
            cellData = col.cell(cellData);
          } else if (cellData instanceof Date) {
            cellData = cellData.toISOString();
          } else if (typeof cellData === "object") {
            cellData = JSON.stringify(cellData);
          }
          return `"${String(cellData ?? "").replace(/"/g, '""')}"`;
        })
        .join(",")
    );

    // Add variation responses for consistency tests
    if (row.testType === "consistency" && row.variationResponses) {
      row.variationResponses.forEach((variation, index) => {
        csvRows.push(
          columns
            .map((col) => {
              let cellData: any;
              switch (col.accessor) {
                case "messageId":
                  cellData = `${row.messageId}_variation_${index + 1}`;
                  break;
                case "response":
                  cellData = variation.response;
                  break;
                case "products":
                  cellData = variation.products;
                  break;
                case "reasoning":
                  cellData = variation.reasoning;
                  break;
                case "followUpQuestion":
                  cellData = variation.followUpQuestion;
                  break;
                case "metadata":
                  cellData = variation.metadata;
                  break;
                default:
                  cellData = row[col.accessor as keyof TransformedData];
              }

              if (col.cell) {
                cellData = col.cell(cellData);
              } else if (cellData instanceof Date) {
                cellData = cellData.toISOString();
              } else if (typeof cellData === "object") {
                cellData = JSON.stringify(cellData);
              }
              return `"${String(cellData ?? "").replace(/"/g, '""')}"`;
            })
            .join(",")
        );
      });
    }
  });

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
  }
};

export default TestResultCard;
