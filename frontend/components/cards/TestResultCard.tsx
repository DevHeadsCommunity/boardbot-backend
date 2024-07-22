import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { TestCase, TestResult } from "@/types";

const TestResultCard = () => {
  const { state, data, actions } = useTestRunnerContext();

  const transformedData = data.testResults.map((testResult: TestResult) => {
    const testCase = data.testCases.find((testCase: TestCase) => testCase.messageId === testResult.messageId);
    return {
      ...testCase,
      ...testResult,
    };
  });

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

  const onSelectTestResult = (testResult: TestResult & TestCase) => {
    console.log(`Selected test result: ${testResult.messageId}`);
  };

  return (
    <Card className="flex flex-col gap-4 bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">Test Results</h2>
      </div>
      <SortableTable columns={columns} data={transformedData} onRowClick={onSelectTestResult} />
    </Card>
  );
};

export default TestResultCard;
