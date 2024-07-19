import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import { PauseIcon, PlayIcon, RepeatIcon } from "lucide-react";
import React from "react";

interface TestExecutionCardProps {
  architecture: string;
  historyManagement: string;
}

const TestExecutionCard: React.FC<TestExecutionCardProps> = ({ architecture, historyManagement }) => {
  const {state, data, actions} = useTestRunnerContext();
  const passedCount = 1;
  const failedCount = 1;
  const pendingCount = 1;
  const errorCount = 1;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <h2 className="text-lg font-semibold">
          Test Execution: {}
        </h2>
        <div className="flex items-center gap-2">
          {state.testRunnerState === "Running" && (
            <Button variant="ghost" size="icon" onClick={actions.click.pauseTest}>
              <PauseIcon className="w-5 h-5" />
            </Button>
          )}
          {(state.testRunnerState  === "Paused") && (
            <Button
              variant="ghost"
              size="icon"
              onClick={actions.click.resumeTest}
            >
              <PlayIcon className="w-5 h-5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={actions.click.resumeTest}>
            <RepeatIcon className="w-5 h-5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative w-full h-2 bg-muted rounded-full">
          <div
            className="absolute left-0 top-0 h-full bg-primary rounded-full"
            style={{ width: `${data.progress}%` }}
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
              {(1 * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-medium">Average Feature Accuracy:</span>
            <span className="font-medium">
              {(1 * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <div className="text-sm text-muted-foreground">Status: {state.testRunnerState}</div>
      </CardFooter>
    </Card>
  );
};

export default TestExecutionCard;
