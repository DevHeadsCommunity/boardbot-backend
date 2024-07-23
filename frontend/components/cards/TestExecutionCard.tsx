import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TestRunnerState, useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { MessageCircleX, PauseIcon, PlayIcon } from "lucide-react";
import React, { useMemo } from "react";

const TestExecutionCard: React.FC = () => {
  const { state, data, actions } = useTestRunnerContext();

  const { passedCount, failedCount, pendingCount, errorCount } = useMemo(() => {
    return data.testResults.reduce(
      (acc: { passedCount: number; failedCount: number; errorCount: number }, result: { isCorrect: any; error: any }) => {
        if (result.isCorrect) acc.passedCount++;
        else if (!result.isCorrect && !result.error) acc.failedCount++;
        else if (result.error) acc.errorCount++;
        return acc;
      },
      { passedCount: 0, failedCount: 0, pendingCount: data.testCases.length - data.testResults.length, errorCount: 0 }
    );
  }, [data.testResults, data.testCases]);

  const averageProductAccuracy = useMemo(() => {
    const sum = data.testResults.reduce((acc: any, result: { productAccuracy: any }) => acc + result.productAccuracy, 0);
    return data.testResults.length > 0 ? sum / data.testResults.length : 0;
  }, [data.testResults]);

  const averageFeatureAccuracy = useMemo(() => {
    const sum = data.testResults.reduce((acc: any, result: { featureAccuracy: any }) => acc + result.featureAccuracy, 0);
    return data.testResults.length > 0 ? sum / data.testResults.length : 0;
  }, [data.testResults]);

  const renderControlButton = () => {
    switch (state.testRunnerState) {
      case TestRunnerState.Running:
        return (
          <Button variant="ghost" size="icon" onClick={actions.click.pauseTest}>
            <PauseIcon className="h-5 w-5" />
          </Button>
        );
      case TestRunnerState.Paused:
        return (
          <Button variant="ghost" size="icon" onClick={actions.click.resumeTest}>
            <PlayIcon className="h-5 w-5" />
          </Button>
        );
      default:
        return (
          <Button variant="ghost" size="icon" onClick={actions.click.startTest}>
            <PlayIcon className="h-5 w-5" />
          </Button>
        );
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">
          Test Execution: {data.currentTestIndex}/{data.testCases.length}
        </CardTitle>
        <div className="flex items-center gap-2">
          {renderControlButton()}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" onClick={actions.click.stopTest}>
                  <MessageCircleX className="h-5 w-5" />
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
        <AccuracyItem label="Average Product Accuracy" value={averageProductAccuracy} />
        <AccuracyItem label="Average Feature Accuracy" value={averageFeatureAccuracy} />
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
