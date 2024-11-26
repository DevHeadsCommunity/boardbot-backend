import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TestRunnerState, useTestRunnerContext } from "@/hooks/useTestRunnerContext";
import {
  AccuracyTestResult,
  ConsistencyTestResult,
  ContextRetentionTestResult,
  ConversationalFlowTestResult,
  DefensibilityTestResult,
  FeatureInferenceTestResult,
  RobustnessTestResult,
} from "@/types";
import { CircleStop, PauseIcon, PlayIcon } from "lucide-react";
import React, { useMemo } from "react";

// Add these helper functions before the TestExecutionCard component
const calculateCost = (metadata: any) => {
  if (!metadata) return 0;
  const inputTokens = metadata?.inputTokenUsage ? Object.values(metadata.inputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
  const outputTokens = metadata?.outputTokenUsage ? Object.values(metadata.outputTokenUsage).reduce((sum, tokens) => sum + tokens, 0) : 0;
  return inputTokens * 0.0000025 + outputTokens * 0.00001;
};

const calculateTotalResponseTime = (consistencyResult: ConsistencyTestResult) => {
  // Calculate main prompt response time
  const mainMetadata = consistencyResult.mainPromptResponse.message.metadata;
  const mainResponseTime = mainMetadata?.timeTaken ? Object.values(mainMetadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;

  // Calculate variations response time
  const variationResponseTime = consistencyResult.variationResponses.reduce((acc, response) => {
    const varMetadata = response.message.metadata;
    const varResponseTime = varMetadata?.timeTaken ? Object.values(varMetadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
    return acc + varResponseTime;
  }, 0);

  // Calculate average response time across all prompts
  const promptCount = 1 + consistencyResult.variationResponses.length;
  return (mainResponseTime + variationResponseTime) / promptCount;
};

const calculateTotalCost = (consistencyResult: ConsistencyTestResult) => {
  // Calculate main prompt cost
  const mainMetadata = consistencyResult.mainPromptResponse.message.metadata;
  const mainCost = calculateCost(mainMetadata);

  // Calculate variations cost
  const variationCost = consistencyResult.variationResponses.reduce((acc, response) => {
    const varMetadata = response.message.metadata;
    return acc + calculateCost(varMetadata);
  }, 0);

  return mainCost + variationCost;
};

const calculateFeatureInferenceMetrics = (testResults: FeatureInferenceTestResult[]) => {
  return testResults.reduce(
    (acc, result) => {
      const metadata = result.response.message.metadata;
      const responseTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
      const cost = calculateCost(metadata);

      return {
        filterAccuracy: acc.filterAccuracy + result.filterAccuracy,
        responseTime: acc.responseTime + responseTime,
        cost: acc.cost + cost,
        totalCost: acc.totalCost + cost,
      };
    },
    { filterAccuracy: 0, responseTime: 0, cost: 0, totalCost: 0 }
  );
};

const calculateContextRetentionMetrics = (testResults: ContextRetentionTestResult[]) => {
  return testResults.reduce(
    (acc, result) => {
      const totalResponseTime =
        result.conversation.reduce((time, turn) => {
          const metadata = turn.message.metadata;
          const turnTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, t) => sum + t, 0) : 0;
          return time + turnTime;
        }, 0) / result.conversation.length;

      const totalCost = result.conversation.reduce((cost, turn) => {
        const metadata = turn.message.metadata;
        return cost + calculateCost(metadata);
      }, 0);

      return {
        contextAccuracy: acc.contextAccuracy + result.contextAccuracy,
        responseTime: acc.responseTime + totalResponseTime,
        cost: acc.cost + totalCost,
        totalCost: acc.totalCost + totalCost,
        turnCount: acc.turnCount + result.conversation.length,
      };
    },
    { contextAccuracy: 0, responseTime: 0, cost: 0, totalCost: 0, turnCount: 0 }
  );
};

// Add new MetricDisplay component at the top level
interface MetricDisplayProps {
  metrics: Record<string, number>;
  totalCost: number;
}

const MetricDisplay = React.memo(function MetricDisplay({ metrics, totalCost }: MetricDisplayProps) {
  return (
    <>
      {Object.entries(metrics).map(([label, value]) => (
        <MetricItem
          key={label}
          label={label}
          value={value as number}
          unit={label.toLowerCase().includes("cost") ? "$" : label.toLowerCase().includes("time") ? "sec" : undefined}
        />
      ))}
      {totalCost > 0 && <MetricItem label="Total Cost" value={totalCost} unit="$" />}
    </>
  );
});

const StatusGrid = React.memo(function StatusGrid({
  pendingCount,
  passedCount,
  failedCount,
  errorCount,
}: {
  pendingCount: number;
  passedCount: number;
  failedCount: number;
  errorCount: number;
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <StatusItem color="gray" label="Pending" count={pendingCount} />
      <StatusItem color="green" label="Passed" count={passedCount} />
      <StatusItem color="yellow" label="Failed" count={failedCount} />
      <StatusItem color="red" label="Errors" count={errorCount} />
    </div>
  );
});

const TestStatus = React.memo(function TestStatus({
  state,
  isConversationalTest,
  currentTestIndex,
}: {
  state: TestRunnerState;
  isConversationalTest: boolean;
  currentTestIndex: number;
}) {
  return (
    <div className="text-sm text-muted-foreground">
      {state === TestRunnerState.Running ? (isConversationalTest ? `Processing conversation turn ${currentTestIndex + 1}` : "Processing test case...") : `Status: ${state}`}
    </div>
  );
});

const TestExecutionCard: React.FC = () => {
  const { state, data, actions } = useTestRunnerContext();

  const { passedCount, failedCount, pendingCount, errorCount } = useMemo(() => {
    if (!data.testCases || !data.testResults) return { passedCount: 0, failedCount: 0, pendingCount: 0, errorCount: 0 };
    const testType = data.testCases[0]?.testType;
    const totalTests = data.testCases.length;
    const completedTests = data.testResults.length;
    const pendingTests = totalTests - completedTests;
    let passed = 0;
    let failed = 0;

    data.testResults.forEach((result) => {
      switch (testType) {
        case "accuracy":
          const accuracyResult = result as AccuracyTestResult;
          if (accuracyResult.productAccuracy > 0.4) passed++;
          else failed++;
          break;
        case "consistency":
          const consistencyResult = result as ConsistencyTestResult;
          if (consistencyResult.productConsistency >= 0.4) passed++;
          else failed++;
          break;
        case "feature_inference":
          const featureResult = result as FeatureInferenceTestResult;
          if (featureResult.filterAccuracy >= 0.4) passed++;
          else failed++;
          break;
        case "context_retention":
          const contextResult = result as ContextRetentionTestResult;
          if (contextResult.contextAccuracy >= 0.4) passed++;
          else failed++;
          break;
        case "robustness":
          const robustnessResult = result as RobustnessTestResult;
          if (robustnessResult.noiseFiltering >= 0.4) passed++;
          else failed++;
          break;
        case "conversational_flow":
          const flowResult = result as ConversationalFlowTestResult;
          if (flowResult.flowCoherence >= 0.4 && flowResult.topicTransitionAccuracy >= 0.4) passed++;
          else failed++;
          break;
        case "defensibility":
          const defensibilityResult = result as DefensibilityTestResult;
          if (defensibilityResult.boundaryMaintenance >= 0.4) passed++;
          else failed++;
          break;
      }
    });

    return {
      passedCount: passed,
      failedCount: failed,
      pendingCount: pendingTests,
      errorCount: 0,
    };
  }, [data.testResults, data.testCases]);

  const calculateMetrics = useMemo(() => {
    if (!data.testCases || !data.testResults || data.testResults.length === 0) {
      return {
        metrics: {},
        totalCost: 0,
      };
    }

    const testType = data.testCases[0]?.testType;
    let metrics = {};
    let totalCost = 0;

    switch (testType) {
      case "accuracy":
        const accuracyMetrics = data.testResults.reduce(
          (acc, result) => {
            const accuracyResult = result as AccuracyTestResult;
            const metadata = accuracyResult.response.message.metadata;
            const responseTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
            const cost = calculateCost(metadata);
            totalCost += cost;

            return {
              productAccuracy: acc.productAccuracy + accuracyResult.productAccuracy,
              responseTime: acc.responseTime + responseTime,
              cost: acc.cost + cost,
            };
          },
          { productAccuracy: 0, responseTime: 0, cost: 0 }
        );

        metrics = {
          "Average Product Accuracy": accuracyMetrics.productAccuracy / data.testResults.length,
          "Average Response Time": accuracyMetrics.responseTime / data.testResults.length,
          "Average Cost": accuracyMetrics.cost / data.testResults.length,
        };
        break;

      case "consistency":
        const consistencyMetrics = data.testResults.reduce(
          (acc, result) => {
            const consistencyResult = result as ConsistencyTestResult;
            const mainMetadata = consistencyResult.mainPromptResponse.message.metadata;
            const responseTime = calculateTotalResponseTime(consistencyResult);
            const cost = calculateTotalCost(consistencyResult);
            totalCost += cost;

            return {
              productConsistency: acc.productConsistency + consistencyResult.productConsistency,
              orderConsistency: acc.orderConsistency + consistencyResult.orderConsistency,
              responseTime: acc.responseTime + responseTime,
              cost: acc.cost + cost,
            };
          },
          { productConsistency: 0, orderConsistency: 0, responseTime: 0, cost: 0 }
        );

        metrics = {
          "Average Product Consistency": consistencyMetrics.productConsistency / data.testResults.length,
          "Average Order Consistency": consistencyMetrics.orderConsistency / data.testResults.length,
          "Average Response Time": consistencyMetrics.responseTime / data.testResults.length,
          "Average Cost": consistencyMetrics.cost / data.testResults.length,
        };
        break;

      case "feature_inference": {
        const featureMetrics = calculateFeatureInferenceMetrics(data.testResults as FeatureInferenceTestResult[]);
        metrics = {
          "Filter Accuracy": featureMetrics.filterAccuracy / data.testResults.length,
          "Average Response Time": featureMetrics.responseTime / data.testResults.length,
          "Average Cost": featureMetrics.cost / data.testResults.length,
        };
        totalCost = featureMetrics.totalCost;
        break;
      }

      case "context_retention": {
        const contextMetrics = calculateContextRetentionMetrics(data.testResults as ContextRetentionTestResult[]);

        metrics = {
          "Context Accuracy": contextMetrics.contextAccuracy / data.testResults.length,
          "Average Turn Count": contextMetrics.turnCount / data.testResults.length,
          "Average Response Time": contextMetrics.responseTime / data.testResults.length,
          "Average Cost per Test": contextMetrics.cost / data.testResults.length,
        };
        totalCost = contextMetrics.totalCost;
        break;
      }

      case "robustness": {
        const robustnessMetrics = data.testResults.reduce(
          (accuracy, result) => {
            const robustnessResult = result as RobustnessTestResult;
            const metadata = robustnessResult.response.message.metadata;
            const responseTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, time) => sum + time, 0) : 0;
            const cost = calculateCost(metadata);
            totalCost += cost;

            return {
              filterAccuracy: accuracy.filterAccuracy + robustnessResult.filterAccuracy,
              noiseFiltering: accuracy.noiseFiltering + robustnessResult.noiseFiltering,
              responseTime: accuracy.responseTime + responseTime,
              cost: accuracy.cost + cost,
            };
          },
          { filterAccuracy: 0, noiseFiltering: 0, responseTime: 0, cost: 0 }
        );

        metrics = {
          "Average Filter Accuracy": robustnessMetrics.filterAccuracy / data.testResults.length,
          "Average Noise Filtering": robustnessMetrics.noiseFiltering / data.testResults.length,
          "Average Response Time": robustnessMetrics.responseTime / data.testResults.length,
          "Average Cost": robustnessMetrics.cost / data.testResults.length,
        };
        break;
      }

      case "defensibility": {
        const defensibilityMetrics = data.testResults.reduce(
          (acc, result) => {
            const defensibilityResult = result as DefensibilityTestResult;
            const responseTime = defensibilityResult.conversation.reduce((time, turn) => {
              const metadata = turn.message.metadata;
              const turnTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, t) => sum + t, 0) : 0;
              return time + turnTime;
            }, 0) / defensibilityResult.conversation.length;

            const cost = defensibilityResult.conversation.reduce((total, turn) => {
              const metadata = turn.message.metadata;
              return total + calculateCost(metadata);
            }, 0);

            totalCost += cost;

            return {
              boundaryMaintenance: acc.boundaryMaintenance + defensibilityResult.boundaryMaintenance,
              responseTime: acc.responseTime + responseTime,
              cost: acc.cost + cost,
            };
          },
          { boundaryMaintenance: 0, responseTime: 0, cost: 0 }
        );

        metrics = {
          "Boundary Maintenance": defensibilityMetrics.boundaryMaintenance / data.testResults.length,
          "Average Response Time": defensibilityMetrics.responseTime / data.testResults.length,
          "Average Cost": defensibilityMetrics.cost / data.testResults.length,
        };
        break;
      }

      case "conversational_flow": {
        const flowMetrics = data.testResults.reduce(
          (acc, result) => {
            const flowResult = result as ConversationalFlowTestResult;
            const responseTime = flowResult.conversation.reduce((time, turn) => {
              const metadata = turn.message.metadata;
              const turnTime = metadata?.timeTaken ? Object.values(metadata.timeTaken).reduce((sum, t) => sum + t, 0) : 0;
              return time + turnTime;
            }, 0) / flowResult.conversation.length;

            const cost = flowResult.conversation.reduce((total, turn) => {
              const metadata = turn.message.metadata;
              return total + calculateCost(metadata);
            }, 0);

            totalCost += cost;

            return {
              flowCoherence: acc.flowCoherence + flowResult.flowCoherence,
              topicTransitionAccuracy: acc.topicTransitionAccuracy + flowResult.topicTransitionAccuracy,
              responseTime: acc.responseTime + responseTime,
              cost: acc.cost + cost,
            };
          },
          { flowCoherence: 0, topicTransitionAccuracy: 0, responseTime: 0, cost: 0 }
        );

        metrics = {
          "Flow Coherence": flowMetrics.flowCoherence / data.testResults.length,
          "Topic Transition Accuracy": flowMetrics.topicTransitionAccuracy / data.testResults.length,
          "Average Response Time": flowMetrics.responseTime / data.testResults.length,
          "Average Cost": flowMetrics.cost / data.testResults.length,
        };
        break;
      }
    }

    return { metrics, totalCost };
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

  const isConversationalTest = useMemo(() => {
    return ["context_retention", "conversational_flow", "defensibility"].includes(data.testCases?.[0]?.testType);
  }, [data.testCases]);

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
        <Progress value={data.progress} className="w-full transition-all duration-300" />
        <StatusGrid pendingCount={pendingCount} passedCount={passedCount} failedCount={failedCount} errorCount={errorCount} />
        <Separator className="my-4" />
        <MetricDisplay metrics={calculateMetrics.metrics} totalCost={calculateMetrics.totalCost} />
      </CardContent>
      <CardFooter>
        <TestStatus state={state.testRunnerState} isConversationalTest={isConversationalTest} currentTestIndex={data.currentTestIndex} />
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

interface MetricItemProps {
  label: string;
  value: number;
  unit?: string;
}

const MetricItem: React.FC<MetricItemProps> = ({ label, value, unit }) => {
  const getScoreColor = (value: number) => {
    if (label.toLowerCase().includes("cost") || label.toLowerCase().includes("time")) {
      return ""; // No color for cost and time metrics
    }
    const score = value * 100;
    if (score >= 90) return "text-green-600";
    if (score >= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const formattedValue = unit === "$" ? `$${value.toFixed(2)}` : unit === "sec" ? `${value.toFixed(2)} sec` : `${(value * 100).toFixed(2)}%`;

  return (
    <div className="flex items-center justify-between">
      <span className="font-medium">{label}:</span>
      <span className={`font-medium ${getScoreColor(value)}`}>{formattedValue}</span>
    </div>
  );
};

export default TestExecutionCard;
