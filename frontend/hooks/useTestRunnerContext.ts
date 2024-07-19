import { AppContext } from "@/context/appContext";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useToast } from "./useToast";

export enum TestRunnerState {
  Idle = "Idle",
  Running = "Running",
  Paused = "Paused",
  Completed = "Completed"
}

export const useTestRunnerContext = () => {
  const state = AppContext.useSelector((state) => state);
  const testActorRef = state.context.testRef;
  const testActorState = useSelector(testActorRef, (state) => state);
  const testRunnerActorRef = testActorState?.context.selectedTest?.testRunnerRef ?? undefined;
  const testRunnerActorState = useSelector(testRunnerActorRef, (state) => state);
  useToast(testRunnerActorRef);

  const testRunnerState = useMemo(() => {
    if (!testRunnerActorState) return TestRunnerState.Idle;
    if (testRunnerActorState.matches('RunningTest')) return TestRunnerState.Running;
    if (testRunnerActorState.matches('TestPaused')) return TestRunnerState.Paused;
    if (testRunnerActorState.matches('TestCompleted')) return TestRunnerState.Completed;
    return TestRunnerState.Idle;
  }, [testRunnerActorState]);

  const handleStartTest = useCallback(() => {
    testRunnerActorRef?.send({ type: "user.startTest" });
  }, [testRunnerActorRef]);
  const handleStopTest = useCallback(() => {
    testRunnerActorRef?.send({ type: "user.stopTest" });
  }, [testRunnerActorRef]);
  const handlePauseTest = useCallback(() => {
    testRunnerActorRef?.send({ type: "user.pauseTest" });
  }, [testRunnerActorRef]);
  const handleResumeTest = useCallback(() => {
    testRunnerActorRef?.send({ type: "user.continueTest" });
  }, [testRunnerActorRef]);


  return {
    state: {
      testRunnerState
    },
    data: {
      testCases: useSelector(testRunnerActorRef, (state: any) => state.context.testCases || []),
      testResults: useSelector(testRunnerActorRef, (state: any) => state.context.testResults || []),
      fullTestResult: useSelector(testRunnerActorRef, (state: any) => state.context.fullTestResult || null),
      currentTestIndex: useSelector(testRunnerActorRef, (state: any) => state.context.currentTestIndex || 0),
      progress: useSelector(testRunnerActorRef, (state: any) => state.context.progress || 0),
    },
    actions: {
      click: {
        startTest: handleStartTest,
        stopTest: handleStopTest,
        pauseTest: handlePauseTest,
        resumeTest: handleResumeTest,
      }
    }
  }
}

export type TestRunnerData = ReturnType<typeof useTestRunnerContext>['data'];
export type TestRunnerActions = ReturnType<typeof useTestRunnerContext>['actions'];
