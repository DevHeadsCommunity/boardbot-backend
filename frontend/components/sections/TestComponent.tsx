"use client";

import CreateTestCard from "@/components/cards/CreateTestCard";
import TestExecutionCard from "@/components/cards/TestExecutionCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Test } from "@/types/Test";

import { TestResult } from "@/types";
import {
  ClipboardIcon,
  DownloadIcon,
  ImportIcon,
  SettingsIcon,
} from "lucide-react";
import { useState } from "react";
import TestListCard from "../cards/TestListCard";
import TestResultCard from "../cards/TestResultCard";

export default function TestComponent() {
  const [tests, setTests] = useState<Test[]>([]);
  const [selectedTest, setSelectedTest] = useState<Test | undefined>(undefined);

  const addTest = (test: Test) => {
    setTests((prevTests) => [...prevTests, test]);
  };

  const onTestComplete = (completedTest: Test) => {
    setTests((prevTests) =>
      prevTests.map((test) =>
        test.id === completedTest.id ? completedTest : test
      )
    );
    setSelectedTest(undefined);
  };

  const onTestResultSelect = (testResult: TestResult) => {
    console.log(`Selected test result: ${testResult.id}`);
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <header className="bg-card px-4 py-3 sm:px-6 flex items-center justify-between border-b">
        <div className="flex items-center gap-4">
          <ClipboardIcon className="w-6 h-6 text-card-foreground" />
          <h1 className="text-lg font-semibold text-card-foreground">
            Test Case Manager
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon">
            <DownloadIcon className="w-5 h-5 text-card-foreground" />
          </Button>
          <Button variant="ghost" size="icon">
            <ImportIcon className="w-5 h-5 text-card-foreground" />
          </Button>
          <Button variant="ghost" size="icon">
            <SettingsIcon className="w-5 h-5 text-card-foreground" />
          </Button>
        </div>
      </header>
      <main className="flex-1 px-4 py-8 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CreateTestCard addTest={addTest} />
          <TestListCard tests={tests} onTestSelect={setSelectedTest} />
          {selectedTest && (
            <TestExecutionCard
              test={selectedTest}
              onTestComplete={onTestComplete}
            />
          )}
        </div>
        <div className="mt-8">
          <Card className="bg-card p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-card-foreground">
                Test Results
              </h2>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon">
                  <DownloadIcon className="w-5 h-5 text-card-foreground" />
                </Button>
              </div>
            </div>
            <div className="mt-4 overflow-auto">
              {selectedTest?.results && (
                <TestResultCard
                  test={selectedTest}
                  onTestResultSelect={onTestResultSelect}
                />
              )}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
