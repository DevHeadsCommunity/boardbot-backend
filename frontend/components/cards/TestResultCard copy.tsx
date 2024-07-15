import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { TestResult } from "@/types/TestResult";
import { useState } from "react";

const TestResultCard = () => {
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null);
  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Status", accessor: "isCorrect" },
    { header: "Duration", accessor: "totalResponseTime" },
  ];

  const onSelect = (test: TestResult) => {
    setSelectedTest(test);
  };

  const dummyTestResults: TestResult[] = [
    {
      id: "1",
      name: "Test 1",
      input: "input 1",
      expectedOutput: "expected output 1",
      isCorrect: true,
      totalResponseTime: 100,
    },
    {
      id: "2",
      name: "Test 2",
      input: "input 2",
      expectedOutput: "expected output 2",
      isCorrect: false,
      totalResponseTime: 200,
    },
    {
      id: "3",
      name: "Test 3",
      input: "input 3",
      expectedOutput: "expected output 3",
      isCorrect: true,
      totalResponseTime: 300,
    },
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
        data={dummyTestResults}
        onRowClick={onSelect}
      />
    </Card>
  );
};

export default TestResultCard;
