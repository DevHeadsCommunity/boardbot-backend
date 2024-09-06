import { convertStateToString } from "@/lib/stateToStr";
import { accuracyTestRunnerMachine } from "@/machines/accuracyTestRunnerMachine";
import { consistencyTestRunnerMachine } from "@/machines/consistencyTestRunnerMachine";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { ActorRefFrom } from "xstate";
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

const stateMap: Record<string, TestRunnerState> = {
  idle: TestRunnerState.Idle,
  connecting: TestRunnerState.Connecting,
  "running.sendingMessage": TestRunnerState.Running,
  "running.paused": TestRunnerState.Paused,
  "running.evaluatingResults": TestRunnerState.Evaluating,
  disconnecting: TestRunnerState.Disconnecting,
};

type TestRunnerAction = { type: "user.startTest" } | { type: "user.stopTest" } | { type: "user.pauseTest" } | { type: "user.continueTest" };

export const useTestRunnerContext = () => {
  const { actorRef } = useAppContext();
  const testActorRef = actorRef.test;
  const testActorState = useSelector(testActorRef, (state) => state);
  const testRunnerActorRef = testActorState?.context.selectedTest?.testRunnerRef as
    | ActorRefFrom<typeof accuracyTestRunnerMachine | typeof consistencyTestRunnerMachine>
    | undefined;
  const testRunnerActorState = useSelector(testRunnerActorRef, (state) => state);
  useToast(testRunnerActorRef);

  const testRunnerState = useMemo(() => {
    console.log(`-----> testRunnerActorState: ${JSON.stringify(testRunnerActorState.value)}`);
    if (!testRunnerActorState) return TestRunnerState.Idle;
    let stateValue = testRunnerActorState.value as string;
    if (typeof stateValue !== "string") {
      stateValue = convertStateToString(stateValue);
    }
    console.log(`-----> stateValue: ${stateValue}`);
    return stateMap[stateValue] || TestRunnerState.Idle;
  }, [testRunnerActorState]);

  const testRunnerDispatch = useCallback(
    (action: TestRunnerAction) => {
      testRunnerActorRef?.send(action);
    },
    [testRunnerActorRef]
  );

  return {
    state: {
      testRunnerState,
    },
    data: {
      name: useSelector(testRunnerActorRef, (state) => state?.context.name),
      testCases: useSelector(testRunnerActorRef, (state) => state?.context.testCases),
      testResults: useSelector(testRunnerActorRef, (state) => state?.context.testResults),
      currentTestIndex: useSelector(testRunnerActorRef, (state) => state?.context.currentTestIndex),
      progress: useSelector(testRunnerActorRef, (state) => state?.context.progress),
    },
    actions: {
      startTest: () => testRunnerDispatch({ type: "user.startTest" }),
      stopTest: () => testRunnerDispatch({ type: "user.stopTest" }),
      pauseTest: () => testRunnerDispatch({ type: "user.pauseTest" }),
      resumeTest: () => testRunnerDispatch({ type: "user.continueTest" }),
    },
  };
};

export type TestRunnerData = ReturnType<typeof useTestRunnerContext>["data"];
export type TestRunnerActions = ReturnType<typeof useTestRunnerContext>["actions"];
