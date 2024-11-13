import SortableTable, { TableColumn } from "@/components/blocks/SortableTable";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTestContext } from "@/hooks/useTestContext";
import { Test, TEST_TYPES } from "@/types";
import React, { useMemo, useState } from "react";

const TestListCard: React.FC = () => {
  const { data, actions } = useTestContext();
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  const columns: TableColumn[] = [
    { header: "Name", accessor: "name" },
    { header: "Type", accessor: "testType" },
    { header: "Created At", accessor: "createdAt" },
    { header: "Status", accessor: "status" },
  ];

  const getTestStatus = (test: Test): "pending" | "running" | "completed" | "error" => {
    const snapshot = test.testRunnerRef.getSnapshot();

    if (!snapshot || typeof snapshot.matches !== "function") {
      return "pending";
    }

    try {
      if (snapshot.matches("idle")) return "pending";
      if (snapshot.matches("running")) return "running";
      if (snapshot.matches("disconnecting") || snapshot.matches("idle")) return "completed";
      return "error";
    } catch (error) {
      console.error("Error checking test status:", error);
      return "error";
    }
  };

  const transformedTests = useMemo(() => {
    return data.tests.map((test) => ({
      ...test,
      testType: test.testType,
      createdAt: new Date(test.createdAt).toLocaleString(),
      status: getTestStatus(test),
    }));
  }, [data.tests]);

  const filteredTests = useMemo(() => {
    return transformedTests.filter((test) => {
      const matchesSearch = test.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === "all" || test.testType === filterType;
      return matchesSearch && matchesType;
    });
  }, [transformedTests, searchTerm, filterType]);

  const handleSelectTest = (test: Test) => {
    actions.select.test(test.testId);
  };

  return (
    <Card className="flex flex-col gap-4 bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">Tests</h2>
      </div>
      <div className="flex gap-4">
        <Input placeholder="Search tests..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="max-w-sm" />
        <Select value={filterType} onValueChange={(value: string) => setFilterType(value)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            {TEST_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {type.replace("_", " ").replace(/^\w/, (c) => c.toUpperCase())}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <SortableTable columns={columns} data={filteredTests} onRowClick={handleSelectTest} />
    </Card>
  );
};

const StatusBadge: React.FC<{ status: "pending" | "running" | "completed" | "error" }> = ({ status }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-500";
      case "running":
        return "bg-blue-500";
      case "completed":
        return "bg-green-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return <Badge className={`${getStatusColor(status)} text-white`}>{status.charAt(0).toUpperCase() + status.slice(1)}</Badge>;
};

export default TestListCard;
