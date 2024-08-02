import { testMachine } from "@/machines/testMachine";
import { TestCase } from "@/types";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { StateFrom } from "xstate";
import { useAppContext } from "./useAppContext";
import { useToast } from "./useToast";

export enum TestState {
  Idle = "Idle",
  DisplayingTest = "DisplayingTest",
  DisplayingTestPage = "DisplayingTestPage",
  DisplayingSelectedTest = "DisplayingSelectedTest",
  DisplayingTestDetailsModal = "DisplayingTestDetailsModal",
  RunningTest = "RunningTest",
}

const testStateMap: Record<keyof StateFrom<typeof testMachine> | string, TestState> = {
  idle: TestState.Idle,
  DisplayingTest: TestState.DisplayingTest,
  "DisplayingTest.Connected.DisplayingTestPage": TestState.DisplayingTestPage,
  "DisplayingTest.Connected.DisplayingTestDetails.DisplayingSelectedTest": TestState.DisplayingSelectedTest,
  "DisplayingTest.Connected.DisplayingTestDetails.DisplayingTestDetailsModal": TestState.DisplayingTestDetailsModal,
  "DisplayingTest.Connected.DisplayingTestDetails.RunningTest": TestState.RunningTest,
};

export const useTestContext = () => {
  const { actorRef } = useAppContext();
  const testActorRef = actorRef.test;
  const testActorState = useSelector(testActorRef, (state) => state);
  useToast(testActorRef);

  const testState = useMemo(() => {
    if (!testActorState) return TestState.Idle;
    const currentState = testActorState.value as string;
    return testStateMap[currentState] || TestState.Idle;
  }, [testActorState]);

  const handleStartTest = useCallback(() => {
    testActorRef?.send({ type: "app.startTest" });
  }, [testActorRef]);
  const handleStopTest = useCallback(() => {
    testActorRef?.send({ type: "app.stopTest" });
  }, [testActorRef]);
  const handleCreateTest = useCallback(
    (data: { name: string; id: string; testCase: TestCase[]; createdAt: string }) => {
      testActorRef?.send({ type: "user.createTest", data: data });
    },
    [testActorRef]
  );
  const handleSelectSingleTestResult = useCallback(() => {
    testActorRef?.send({ type: "user.clickSingleTestResult" });
  }, [testActorRef]);
  const handleCloseTestResultModal = useCallback(() => {
    testActorRef?.send({ type: "user.closeTestResultModal" });
  }, [testActorRef]);
  const handleSelectTest = useCallback(
    (testId: string) => {
      testActorRef?.send({ type: "user.selectTest", data: { testId } });
    },
    [testActorRef]
  );

  return {
    state: {
      testState,
    },
    data: {
      tests: useSelector(testActorRef, (state) => state?.context.tests || []),
      selectedTest: useSelector(testActorRef, (state) => state?.context.selectedTest || null),
    },
    actions: {
      click: {
        startTest: handleStartTest,
        stopTest: handleStopTest,
        createTest: handleCreateTest,
      },
      select: {
        test: handleSelectTest,
        testResult: handleSelectSingleTestResult,
      },
      close: {
        testResultModal: handleCloseTestResultModal,
      },
    },
  };
};

export type TestData = ReturnType<typeof useTestContext>["data"];
export type TestActions = ReturnType<typeof useTestContext>["actions"];
