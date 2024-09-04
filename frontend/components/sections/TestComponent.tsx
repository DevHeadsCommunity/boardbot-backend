"use client";

import CreateTestCard from "@/components/cards/CreateTestCard";
import TestExecutionCard from "@/components/cards/TestExecutionCard";
import { useTestContext } from "@/hooks/useTestContext";
import { FlaskConical } from "lucide-react";
import TestListCard from "../cards/TestListCard";
import TestResultCard from "../cards/TestResultCard";

export default function TestComponent() {
  const { state, data, actions } = useTestContext();

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between bg-card px-6 py-8 ">
        <div className="flex items-center gap-4">
          <FlaskConical className="h-6 w-6 text-card-foreground" />
          <h1 className="text-lg font-semibold text-card-foreground">Test Case Manager</h1>
        </div>
      </header>

      <main className="flex-1 px-4 pb-8 sm:px-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <CreateTestCard />
          <TestListCard />
          {data.selectedTest && <TestExecutionCard />}
        </div>
        {data.selectedTest && <TestResultCard />}
      </main>
    </div>
  );
}
