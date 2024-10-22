import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TestRunnerState, useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { AccuracyTestResult, ConsistencyTestResult } from "@/types";
import { CircleStop, PauseIcon, PlayIcon } from "lucide-react";
import React, { useMemo } from "react";

const TestExecutionCard: React.FC = () => {
  const { state, data, actions } = useTestRunnerContext();

  const { passedCount, failedCount, pendingCount, errorCount } = useMemo(() => {
    if (!data.testCases || !data.testResults) return { passedCount: 0, failedCount: 0, pendingCount: 0, errorCount: 0 };
    if (data.testCases[0]?.testType === "accuracy") {
      return data.testResults.reduce(
        (acc, result) => {
          const accuracyResult = result as AccuracyTestResult;
          if (accuracyResult.productAccuracy > 0.4) acc.passedCount++;
          else acc.failedCount++;
          return acc;
        },
        { passedCount: 0, failedCount: 0, pendingCount: data.testCases.length - data.testResults.length, errorCount: 0 }
      );
    } else {
      return data.testResults.reduce(
        (acc, result) => {
          const consistencyResult = result as ConsistencyTestResult;
          if (consistencyResult.productConsistency >= 0.5 && consistencyResult.orderConsistency >= 0.5) acc.passedCount++;
          else acc.failedCount++;
          return acc;
        },
        { passedCount: 0, failedCount: 0, pendingCount: data.testCases.length - data.testResults.length, errorCount: 0 }
      );
    }
  }, [data.testResults, data.testCases]);

  const averageMetrics = useMemo(() => {
    if (!data.testCases || !data.testResults) return {};
    if (data.testCases[0]?.testType === "accuracy") {
      const sum = data.testResults.reduce(
        (acc, result) => {
          const accuracyResult = result as AccuracyTestResult;
          return {
            productAccuracy: acc.productAccuracy + accuracyResult.productAccuracy,
            featureAccuracy: acc.featureAccuracy + accuracyResult.featureAccuracy,
          };
        },
        { productAccuracy: 0, featureAccuracy: 0 }
      );

      return {
        averageProductAccuracy: sum.productAccuracy / data.testResults.length,
        averageFeatureAccuracy: sum.featureAccuracy / data.testResults.length,
      };
    } else {
      const sum = data.testResults.reduce(
        (acc, result) => {
          const consistencyResult = result as ConsistencyTestResult;
          return {
            productConsistency: acc.productConsistency + consistencyResult.productConsistency,
            orderConsistency: acc.orderConsistency + consistencyResult.orderConsistency,
          };
        },
        { productConsistency: 0, orderConsistency: 0 }
      );

      return {
        averageProductConsistency: sum.productConsistency / data.testResults.length,
        averageOrderConsistency: sum.orderConsistency / data.testResults.length,
      };
    }
  }, [data.testResults, data.testCases]);

  const renderControlButton = () => {
    switch (state.testRunnerState) {
      case TestRunnerState.Running:
        return (
          <Button variant="ghost" size="icon" onClick={actions.pauseTest}>
            <PauseIcon className="h-5 w-5" />
          </Button>
        );
      case TestRunnerState.Paused:
        return (
          <Button variant="ghost" size="icon" onClick={actions.resumeTest}>
            <PlayIcon className="h-5 w-5" />
          </Button>
        );
      default:
        return (
          <Button variant="ghost" size="icon" onClick={actions.startTest}>
            <PlayIcon className="h-5 w-5" />
          </Button>
        );
    }
  };

  console.log("===:> TestExecutionCard: TestRunnerState", state);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">
          Test Execution: {data.currentTestIndex}/{data.testCases?.length ?? 0.0000001}
        </CardTitle>
        <div className="flex items-center gap-2">
          {renderControlButton()}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" onClick={actions.stopTest}>
                  <CircleStop className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Stop Test</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={data.progress} className="w-full" />
        <div className="grid grid-cols-2 gap-4">
          <StatusItem color="gray" label="Pending" count={pendingCount} />
          <StatusItem color="green" label="Passed" count={passedCount} />
          <StatusItem color="yellow" label="Failed" count={failedCount} />
          <StatusItem color="red" label="Errors" count={errorCount} />
        </div>

        {data.testCases && data.testCases[0]?.testType === "accuracy" ? (
          <>
            <AccuracyItem label="Average Product Accuracy" value={averageMetrics.averageProductAccuracy ?? 0} />
            <AccuracyItem label="Average Feature Accuracy" value={averageMetrics.averageFeatureAccuracy ?? 0} />
          </>
        ) : (
          <>
            <AccuracyItem label="Average Product Consistency" value={averageMetrics.averageProductConsistency ?? 0} />
            <AccuracyItem label="Average Order Consistency" value={averageMetrics.averageOrderConsistency ?? 0} />
          </>
        )}
      </CardContent>
      <CardFooter>
        <div className="text-sm text-muted-foreground">Status: {state.testRunnerState}</div>
      </CardFooter>
    </Card>
  );
};

interface StatusItemProps {
  color: string;
  label: string;
  count: number;
}

const StatusItem: React.FC<StatusItemProps> = ({ color, label, count }) => (
  <div className="flex items-center gap-2">
    <div className={`h-4 w-4 rounded-full bg-${color}-500`} />
    <span className="font-medium">
      {label}: {count}
    </span>
  </div>
);

interface AccuracyItemProps {
  label: string;
  value: number;
}

const AccuracyItem: React.FC<AccuracyItemProps> = ({ label, value }) => (
  <div className="flex items-center justify-between">
    <span className="font-medium">{label}:</span>
    <span className="font-medium">{(value * 100).toFixed(2)}%</span>
  </div>
);

export default TestExecutionCard;
