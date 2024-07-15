import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Card } from "@/components/ui/card";
import { Test } from "@/types";

type TestListCardProps = {
  tests: Test[];
  onTestSelect: (test: Test) => void;
};

const TestListCard = ({ tests, onTestSelect }: TestListCardProps) => {
  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Status", accessor: "isCorrect" },
    { header: "Duration", accessor: "totalResponseTime" },
  ];

  return (
    <Card className="bg-card p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">
          Test Results
        </h2>
      </div>
      <SortableTable columns={columns} data={tests} onRowClick={onTestSelect} />
    </Card>
  );
};

export default TestListCard;
