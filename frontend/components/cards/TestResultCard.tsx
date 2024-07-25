import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { Product, TestCase, TestResult } from "@/types";
import { DownloadIcon } from "lucide-react";
import React, { useState } from "react";
import ChatMessageContent from "../blocks/ChatMessageContent";

type TransformedData = {
  name: string;
  messageId: string;
  input: string;
  actualOutput: string;
  expectedProducts: Product[];
  inputTokenCount: number;
  outputTokenCount: number;
  llmResponseTime: number;
  totalResponseTime: number;
  productAccuracy: number;
  featureAccuracy: number;
  error?: string;
  tags?: string[];
};

const TestResultCard = () => {
  const { state, data, actions } = useTestRunnerContext();
  const [showModal, setShowingModal] = useState(false);
  const [selectedTestResult, setSelectedTestResult] = useState<TransformedData | null>(null);
  console.log("data.testCases: ", data.testCases);
  console.log("data.testResults: ", data.testResults);

  const transformedData = data.testResults.map((testResult: TestResult) => {
    const testCase = data.testCases.find((testCase: TestCase) => testCase.messageId === testResult.messageId);
    console.log("testCase: ", testCase);
    console.log("testResult: ", testResult);
    return {
      name: testCase?.name || "Unnamed Test",
      messageId: testResult.messageId,
      input: testCase?.input || "",
      actualOutput: testResult.actualOutput,
      expectedProducts: testCase?.expectedProducts || [],
      inputTokenCount: testResult.inputTokenCount,
      outputTokenCount: testResult.outputTokenCount,
      llmResponseTime: testResult.llmResponseTime,
      totalResponseTime: testResult.totalResponseTime,
      productAccuracy: testResult.productAccuracy,
      featureAccuracy: testResult.featureAccuracy,
      error: testResult.error,
      tags: testCase?.tags || [],
    };
  });

  console.log("transformedData: ", transformedData);

  const columns: TableColumn[] = [
    { header: "Message ID", accessor: "messageId" },
    { header: "Input Tokens", accessor: "inputTokenCount" },
    { header: "Output Tokens", accessor: "outputTokenCount" },
    { header: "LLM Response Time (ms)", accessor: "llmResponseTime" },
    { header: "Total Response Time (ms)", accessor: "totalResponseTime" },
    { header: "Product Accuracy", accessor: "productAccuracy" },
    { header: "Feature Accuracy", accessor: "featureAccuracy" },
  ];

  const allColumns: TableColumn[] = [
    { header: "Message ID", accessor: "messageId" },
    { header: "Input Tokens", accessor: "inputTokenCount" },
    { header: "Output Tokens", accessor: "outputTokenCount" },
    { header: "LLM Response Time (ms)", accessor: "llmResponseTime" },
    { header: "Total Response Time (ms)", accessor: "totalResponseTime" },
    { header: "Product Accuracy", accessor: "productAccuracy" },
    { header: "Feature Accuracy", accessor: "featureAccuracy" },
    { header: "Input", accessor: "input" },
    { header: "Actual Output", accessor: "actualOutput" },
    { header: "Expected Products", accessor: "expectedProducts" },
    { header: "Error", accessor: "error" },
    { header: "Tags", accessor: "tags" },
  ];

  const downloadCSV = (columns: TableColumn[], transformedData: TransformedData[]) => {
    const headers = columns.map((col) => col.header);
    const csvContent = [
      headers.join(","),
      ...transformedData.map((row: { [x: string]: any }) =>
        columns
          .map((col) => {
            let cellData = row[col.accessor as keyof TransformedData];
            // Handle special cases like objects or arrays
            if (typeof cellData === "object") {
              cellData = JSON.stringify(cellData);
            }
            // Escape commas and quotes
            return `"${String(cellData).replace(/"/g, '""')}"`;
          })
          .join(",")
      ),
    ].join("\n");

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

  const onSelectTestResult = (testResult: TransformedData) => {
    setSelectedTestResult(testResult);
    setShowingModal(true);
  };

  return (
    <div className="mt-8">
      <Card className="bg-card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-card-foreground">Test Results</h2>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => downloadCSV(allColumns, transformedData)}>
              <DownloadIcon className="h-5 w-5 text-card-foreground" />
            </Button>
          </div>
        </div>
        <div className="mt-4 overflow-auto">
          <Card className="flex flex-col gap-4 bg-card p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-card-foreground">{data.name}</h2>
            </div>
            <SortableTable columns={columns} data={transformedData} onRowClick={onSelectTestResult} />
          </Card>
          {selectedTestResult && <ResultModal isOpen={showModal} onClose={() => setShowingModal(false)} data={selectedTestResult} />}
        </div>
      </Card>
    </div>
  );
};

interface ResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TransformedData;
}

const ResultModal: React.FC<ResultModalProps> = ({ isOpen, onClose, data }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Test Result: {data.name}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[80vh] overflow-y-auto">
          <div className="space-y-6 p-4">
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Metrics</h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                <MetricItem label="Message ID" value={data.messageId} />
                <MetricItem label="Input Tokens" value={data.inputTokenCount} />
                <MetricItem label="Output Tokens" value={data.outputTokenCount} />
                <MetricItem label="LLM Response Time" value={`${data.llmResponseTime.toFixed(2)}ms`} />
                {/* <MetricItem label="Total Response Time" value={`${data.totalResponseTime.toFixed(2)}ms`} /> */}
                <MetricItem label="Product Accuracy" value={`${(data.productAccuracy * 100).toFixed(2)}%`} />
                <MetricItem label="Feature Accuracy" value={`${(data.featureAccuracy * 100).toFixed(2)}%`} />
              </div>
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Input</h3>
              <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.input}</pre>
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Actual Output</h3>
              <ChatMessageContent message={data.actualOutput} />
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Expected Products</h3>
              <ChatMessageContent message={JSON.stringify(data.expectedProducts, null, 2)} />
            </Card>
            {data.error && (
              <Card className="bg-muted p-4">
                <h3 className="mb-2 text-lg font-semibold">Error</h3>
                <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.error}</pre>
              </Card>
            )}
            {data.tags && data.tags.length > 0 && (
              <Card className="bg-muted p-4">
                <h3 className="mb-2 text-lg font-semibold">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {data.tags.map((tag, index) => (
                    <span key={index} className="rounded bg-primary/10 px-2 py-1 text-sm">
                      {tag}
                    </span>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </ScrollArea>
        <DialogFooter>
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const MetricItem: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div>
    <p className="text-sm font-medium text-muted-foreground">{label}</p>
    <p className="text-lg font-semibold">{value}</p>
  </div>
);

export default TestResultCard;
