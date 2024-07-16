import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { Test } from "@/types";
import { TestResult } from "@/types/TestResult";

type TestResultCardProps = {
  test: Test;
  onTestResultSelect: (test: TestResult) => void;
};

const TestResultCard = ({ test, onTestResultSelect }: TestResultCardProps) => {
  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Input token", accessor: "inputTokenCount" },
    { header: "Output token", accessor: "outputTokenCount" },
    { header: "LLM response time", accessor: "llmResponseTime" },
    { header: "Total response time", accessor: "totalResponseTime" },
  ];

  return (
    <Card className="bg-card p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">
          Test Results
        </h2>
      </div>
      <SortableTable
        columns={columns}
        data={test?.results!}
        onRowClick={onTestResultSelect}
      />
    </Card>
  );
};

export default TestResultCard;
