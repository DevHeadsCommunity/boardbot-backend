import { testRunnerMachine } from "@/machines/testRunnerMachine";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { StateFrom } from "xstate";
import { useAppContext } from "./useAppContext";
import { useToast } from "./useToast";

export enum TestRunnerState {
  Idle = "Idle",
  Connecting = "Connecting",
  Running = "Running",
  Paused = "Paused",
  Evaluating = "Evaluating",
  Disconnecting = "Disconnecting",
}

const testRunnerStateMap: Record<keyof StateFrom<typeof testRunnerMachine> | string, TestRunnerState> = {
  idle: TestRunnerState.Idle,
  Connecting: TestRunnerState.Connecting,
  "Connected.RunningBatchTest": TestRunnerState.Running,
  "Connected.TestPaused": TestRunnerState.Paused,
  "Connected.EvaluatingFullTestResult": TestRunnerState.Evaluating,
  Disconnecting: TestRunnerState.Disconnecting,
};

export const useTestRunnerContext = () => {
  const { actorRef } = useAppContext();
  const testActorRef = actorRef.test;
  const testActorState = useSelector(testActorRef, (state) => state);
  const testRunnerActorRef = testActorState?.context.selectedTest?.testRunnerRef ?? undefined;
  const testRunnerActorState = useSelector(testRunnerActorRef, (state) => state);
  useToast(testRunnerActorRef);
  const webSocketActorRef = testRunnerActorState?.context.webSocketRef ?? undefined;
  const webSocketActorState = useSelector(webSocketActorRef, (state) => state);
  useToast(webSocketActorRef);

  const testRunnerState = useMemo(() => {
    if (!testRunnerActorState) return TestRunnerState.Idle;
    const currentState = testRunnerActorState.value as string;
    return testRunnerStateMap[currentState] || TestRunnerState.Idle;
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
      testRunnerState,
    },
    data: {
      name: useSelector(testRunnerActorRef, (state: any) => state.context.name || ""),
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
      },
    },
  };
};

export type TestRunnerData = ReturnType<typeof useTestRunnerContext>["data"];
export type TestRunnerActions = ReturnType<typeof useTestRunnerContext>["actions"];
