"use client";

import CreateTestCard from "@/components/cards/CreateTestCard";
import TestExecutionCard from "@/components/cards/TestExecutionCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useTestContext } from "@/hooks/useTestContext";
import { Test, TestCase } from "@/types";
import { DownloadIcon, FlaskConical } from "lucide-react";
import TestListCard from "../cards/TestListCard";
import TestResultCard from "../cards/TestResultCard";

export default function TestComponent() {
  const { state, data, actions } = useTestContext();

  const handleAddTest = (data: { name: string; id: string; testCase: TestCase[]; createdAt: string }) => {
    actions.click.createTest(data);
  };

  const handleSelectTest = (test: Test) => {
    actions.select.test(test.testId);
  };

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
          <CreateTestCard addTest={handleAddTest} />
          <TestListCard tests={data.tests} onTestSelect={handleSelectTest} />
          {data.selectedTest && <TestExecutionCard />}
        </div>
        {data.selectedTest && (
          <div className="mt-8">
            <Card className="bg-card p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-card-foreground">Test Results</h2>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon">
                    <DownloadIcon className="h-5 w-5 text-card-foreground" />
                  </Button>
                </div>
              </div>
              <div className="mt-4 overflow-auto">
                <TestResultCard />
              </div>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
