import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import useTestRunner from "@/hooks/useTestRunner";
import { Test, TestResult } from "@/types";
import { PauseIcon, PlayIcon, RepeatIcon } from "lucide-react";
import React, { useEffect } from "react";

interface TestExecutionCardProps {
  test: Test;
  onTestComplete: (completedTest: Test) => void;
}

const TestExecutionCard: React.FC<TestExecutionCardProps> = ({
  test,
  onTestComplete,
}) => {
  const {
    status,
    currentTest,
    progress,
    startTest,
    pauseTest,
    resumeTest,
    retryFailedTests,
  } = useTestRunner({ test });

  useEffect(() => {
    if (currentTest === undefined) return;
    if (status === "COMPLETED") {
      onTestComplete(currentTest);
    }
  }, [status, currentTest, onTestComplete]);

  const results = currentTest?.results || [];

  const passedCount = results.filter((result) => result.isCorrect).length;
  const failedCount = results.filter((result) => !result.isCorrect).length;
  const pendingCount = (currentTest?.testCases?.length || 0) - results.length;
  const errorCount = results.filter((result) => result.error).length;

  const calculateAverage = (property: keyof TestResult): number => {
    if (results.length === 0) return 0;
    const sum = results.reduce(
      (acc, result) => acc + (result[property] as number),
      0
    );
    return sum / results.length;
  };

  const averageProductAccuracy = calculateAverage("productAccuracy");
  const averageFeatureAccuracy = calculateAverage("featureAccuracy");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <h2 className="text-lg font-semibold">
          Test Execution: {currentTest?.name}
        </h2>
        <div className="flex items-center gap-2">
          {status === "RUNNING" && (
            <Button variant="ghost" size="icon" onClick={pauseTest}>
              <PauseIcon className="w-5 h-5" />
            </Button>
          )}
          {(status === "PAUSED" || status === "PENDING") && (
            <Button
              variant="ghost"
              size="icon"
              onClick={status === "PAUSED" ? resumeTest : startTest}
            >
              <PlayIcon className="w-5 h-5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={retryFailedTests}>
            <RepeatIcon className="w-5 h-5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative w-full h-2 bg-muted rounded-full">
          <div
            className="absolute left-0 top-0 h-full bg-primary rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-500 rounded-full" />
            <span className="font-medium">Pending: {pendingCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded-full" />
            <span className="font-medium">Passed: {passedCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4  bg-yellow-500 rounded-full" />
            <span className="font-medium">Failed: {failedCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded-full" />
            <span className="font-medium">Errors: {errorCount}</span>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">Average Product Accuracy:</span>
            <span className="font-medium">
              {(averageProductAccuracy * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-medium">Average Feature Accuracy:</span>
            <span className="font-medium">
              {(averageFeatureAccuracy * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <div className="text-sm text-muted-foreground">Status: {status}</div>
      </CardFooter>
    </Card>
  );
};

export default TestExecutionCard;
