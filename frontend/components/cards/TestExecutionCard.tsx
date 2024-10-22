import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
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
        {
          passedCount: 0,
          failedCount: 0,
          pendingCount: data.testCases.length - data.testResults.length,
          errorCount: 0,
        }
      );
    } else {
      return data.testResults.reduce(
        (acc, result) => {
          const consistencyResult = result as ConsistencyTestResult;
          if (consistencyResult.productConsistency >= 0.5 && consistencyResult.orderConsistency >= 0.5) acc.passedCount++;
          else acc.failedCount++;
          return acc;
        },
        {
          passedCount: 0,
          failedCount: 0,
          pendingCount: data.testCases.length - data.testResults.length,
          errorCount: 0,
        }
      );
    }
  }, [data.testResults, data.testCases]);

  const averageMetrics = useMemo(() => {
    if (!data.testCases || !data.testResults || data.testResults.length === 0) {
      return {
        averageProductAccuracy: 0,
        averageFeatureAccuracy: 0,
        averageProductConsistency: 0,
        averageOrderConsistency: 0,
        averageResponseTime: 0,
        averageCost: 0,
      };
    }
    if (data.testCases[0]?.testType === "accuracy") {
      const sum = data.testResults.reduce(
        (acc, result) => {
          const accuracyResult = result as AccuracyTestResult;
          const metadata = accuracyResult.response.message.metadata;
          const responseTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
          const inputTokens = metadata?.inputTokenUsage ? Object.values(metadata.inputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
          const outputTokens = metadata?.outputTokenUsage ? Object.values(metadata.outputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
          // $10 per million output tokens, $2.5 per million input tokens
          const cost = inputTokens * 0.0000025 + outputTokens * 0.00001;

          return {
            productAccuracy: acc.productAccuracy + accuracyResult.productAccuracy,
            featureAccuracy: acc.featureAccuracy + accuracyResult.featureAccuracy,
            totalResponseTime: acc.totalResponseTime + responseTime,
            totalCost: acc.totalCost + cost,
          };
        },
        {
          productAccuracy: 0,
          featureAccuracy: 0,
          totalResponseTime: 0,
          totalCost: 0,
        }
      );

      return {
        averageProductAccuracy: sum.productAccuracy / data.testResults.length,
        averageFeatureAccuracy: sum.featureAccuracy / data.testResults.length,
        averageResponseTime: sum.totalResponseTime / data.testResults.length,
        averageCost: sum.totalCost / data.testResults.length,
      };
    } else {
      const sum = data.testResults.reduce(
        (acc, result) => {
          const consistencyResult = result as ConsistencyTestResult;
          const metadata = consistencyResult.mainPromptResponse.message.metadata;
          const responseTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
          const inputTokens = metadata?.inputTokenUsage ? Object.values(metadata.inputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
          const outputTokens = metadata?.outputTokenUsage ? Object.values(metadata.outputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
          // $10 per million output tokens, $2.5 per million input tokens
          const cost = inputTokens * 0.0000025 + outputTokens * 0.00001;

          return {
            productConsistency: acc.productConsistency + consistencyResult.productConsistency,
            orderConsistency: acc.orderConsistency + consistencyResult.orderConsistency,
            totalResponseTime: acc.totalResponseTime + responseTime,
            totalCost: acc.totalCost + cost,
          };
        },
        {
          productConsistency: 0,
          orderConsistency: 0,
          totalResponseTime: 0,
          totalCost: 0,
        }
      );

      return {
        averageProductConsistency: sum.productConsistency / data.testResults.length,
        averageOrderConsistency: sum.orderConsistency / data.testResults.length,
        averageResponseTime: sum.totalResponseTime / data.testResults.length,
        averageCost: sum.totalCost / data.testResults.length,
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

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">
          Test Execution: {data.currentTestIndex}/{data.testCases?.length ?? 0}
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

        <Separator className="my-4" />

        {data.testCases && data.testCases[0]?.testType === "accuracy" ? (
          <>
            <AccuracyItem label="Average Product Accuracy" value={averageMetrics.averageProductAccuracy} />
            {/* <AccuracyItem label="Average Feature Accuracy" value={averageMetrics.averageFeatureAccuracy} /> */}
            <AccuracyItem label="Average Response Time" value={averageMetrics.averageResponseTime} unit="sec" />
            <AccuracyItem label="Average Cost" value={averageMetrics.averageCost} unit="$" />
          </>
        ) : (
          <>
            <AccuracyItem label="Average Product Consistency" value={averageMetrics.averageProductConsistency} />
            <AccuracyItem label="Average Order Consistency" value={averageMetrics.averageOrderConsistency} />
            <AccuracyItem label="Average Response Time" value={averageMetrics.averageResponseTime} unit="sec" />
            <AccuracyItem label="Average Cost" value={averageMetrics.averageCost} unit="$" />
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
  unit?: string;
}

const AccuracyItem: React.FC<AccuracyItemProps> = ({ label, value, unit }) => (
  <div className="flex items-center justify-between">
    <span className="font-medium">{label}:</span>
    <span className="font-medium">{unit === "$" ? `$${value.toFixed(2)}` : unit === "sec" ? `${value.toFixed(2)} sec` : `${(value * 100).toFixed(2)}%`}</span>
  </div>
);

export default TestExecutionCard;
