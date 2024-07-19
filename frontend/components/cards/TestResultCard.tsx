import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { TestActions, TestData, TestExecutionState } from "@/hooks/useTestContext";

type TestResultCardProps = {
  state: TestExecutionState;
  data: TestData;
  actions: TestActions
};

const TestResultCard = ({ state, data, actions }: TestResultCardProps) => {
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
        data={data.testResults}
        onRowClick={actions.handleSelectTest}
      />
    </Card>
  );
};

export default TestResultCard;
