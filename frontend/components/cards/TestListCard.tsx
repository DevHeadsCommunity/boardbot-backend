import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Test } from "@/types";

type TestListCardProps = {
  tests: Test[];
  onTestSelect: (test: Test) => void;
};

type TestStatusProps = {
  status: string;
};

const TestStatus = ({ status }: TestStatusProps) => {
  let color = "";
  let text = "";

  switch (status) {
    case "PENDING":
      color = "yellow";
      text = "Pending";
      break;
    case "RUNNING":
      color = "blue";
      text = "Running";
      break;
    case "COMPLETED":
      color = "green";
      text = "Passed";
      break;
    case "FAILED":
      color = "red";
      text = "Failed";
      break;
    case "PAUSED":
      color = "yellow";
      text = "Paused";
      break;
    default:
      break;
  }

  return (
    <div className={`flex items-center gap-2`}>
      <div className={cn(`h-4 w-4 bg-${color}-500 rounded-full`)} />
      <span className="font-medium">{text}</span>
    </div>
  );
};

const TestListCard = ({ tests, onTestSelect }: TestListCardProps) => {
  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Created At", accessor: "createdAt" },
    { header: "Id", accessor: "testId" },
  ];

  const transformedTests = tests.map((test) => ({
    ...test,
    createdAt: new Date(test.createdAt).toLocaleString(),
  }));

  return (
    <Card className="flex flex-col gap-4 bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">Tests</h2>
      </div>
      <SortableTable columns={columns} data={transformedTests} onRowClick={onTestSelect} />
    </Card>
  );
};

export default TestListCard;
