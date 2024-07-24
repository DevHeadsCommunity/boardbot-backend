import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { TestCase, TestResult } from "@/types";
import { useState } from "react";
import Modal from "../sections/Modal";

// type of transformedData
type TransformedData = {
  name: string;
  inputTokenCount: number;
  outputTokenCount: number;
  llmResponseTime: number;
  totalResponseTime: number;
  productAccuracy: number;
  featureAccuracy: number;
  actualOutput: string;
  expectedOutputs: string;
  status: string;
};

const TestResultCard = () => {
  const { state, data, actions } = useTestRunnerContext();
  const [showModal, setShowingModal] = useState(false);
  const [selectedTestResult, setSelectedTestResult] = useState<TransformedData | null>(null);

  const transformedData = data.testResults.map((testResult: TestResult) => {
    const testCase = data.testCases.find((testCase: TestCase) => testCase.messageId === testResult.messageId);
    console.log("testCase: ", testCase);
    console.log("testResult: ", testResult);
    return {
      ...testCase,
      ...testResult,
    };
  });

  console.log("transformedData: ", transformedData);

  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Input token", accessor: "inputTokenCount" },
    { header: "Output token", accessor: "outputTokenCount" },
    { header: "LLM response time", accessor: "llmResponseTime" },
    { header: "Total response time", accessor: "totalResponseTime" },
    { header: "Product accuracy", accessor: "productAccuracy" },
    { header: "Feature accuracy", accessor: "featureAccuracy" },
    { header: "Status", accessor: "status" },
  ];

  const onSelectTestResult = (testResult: TransformedData) => {
    setSelectedTestResult(testResult);
    setShowingModal(true);
  };

  return (
    <>
      <Card className="flex flex-col gap-4 bg-card p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-card-foreground">Test Results</h2>
        </div>
        <SortableTable columns={columns} data={transformedData} onRowClick={onSelectTestResult} />
      </Card>
      <Modal isOpen={showModal} title="Test Result" content={<ResultComponent data={selectedTestResult!} />} onClose={() => setShowingModal(false)} />
    </>
  );
};

interface ResultComponentProps {
  data: TransformedData;
}

const ResultComponent: React.FC<ResultComponentProps> = ({ data }) => {
  return (
    <Card className="flex flex-col gap-4 bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">Test Result</h2>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Name</h3>
          <p>{data.name}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Input token</h3>
          <p>{data.inputTokenCount}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Output token</h3>
          <p>{data.outputTokenCount}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">LLM response time</h3>
          <p>{data.llmResponseTime}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Total response time</h3>
          <p>{data.totalResponseTime}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Product accuracy</h3>
          <p>{data.productAccuracy}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Feature accuracy</h3>
          <p>{data.featureAccuracy}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Status</h3>
          <p>{data.status}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">LLM Outputs</h3>
          <p>{data.expectedOutputs}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Expected Outputs</h3>
          <p>{data.actualOutput}</p>
        </div>
      </div>
    </Card>
  );
};

export default TestResultCard;
