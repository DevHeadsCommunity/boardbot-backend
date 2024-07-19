import { AppContext } from "@/context/appContext";
import { Test } from "@/types";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useToast } from "./useToast";


export enum TestState {
  Idle = "Idle",
  DisplayingTest = "DisplayingTest",
  DisplayingTestPage = "DisplayingTestPage",
  DisplayingSelectedTest = "DisplayingSelectedTest",
  DisplayingTestDetailsModal = "DisplayingTestDetailsModal",
  RunningTest = "RunningTest"
}

export const useTestContext = () => {
  const state = AppContext.useSelector((state) => state);
  const testActorRef = state.context.testRef;
  const testActorState = useSelector(testActorRef, (state) => state);
  useToast(testActorRef);

    const testState = useMemo(() => {
      if (!testActorState) return TestState.Idle;
      if (testActorState.matches('DisplayingTest')) return TestState.DisplayingTest;
      if (testActorState.matches('DisplayingTest.Connected.DisplayingTestPage' as any)) return TestState.DisplayingTestPage;
      if (testActorState.matches('DisplayingTest.Connected.DisplayingTestDetails.DisplayingSelectedTest' as any)) return TestState.DisplayingSelectedTest;
      if (testActorState.matches('DisplayingTest.Connected.DisplayingTestDetails.DisplayingTestDetailsModal' as any)) return TestState.DisplayingTestDetailsModal;
      if (testActorState.matches('DisplayingTest.Connected.DisplayingTestDetails.RunningTest' as any)) return TestState.RunningTest;
    }, [testActorState]);


  const handleStartTest = useCallback(() => {
    testActorRef?.send({ type: "app.startTest" });
  }, [testActorRef]);
  const handleStopTest = useCallback(() => {
    testActorRef?.send({ type: "app.stopTest" });
  }, [testActorRef]);
  const handleCreateTest = useCallback((data: Test) => {
    testActorRef?.send({ type: "user.createTest", data });
  }, [testActorRef]);
  const handleSelectSingleTestResult = useCallback(() => {
    testActorRef?.send({ type: "user.clickSingleTestResult" });
  }, [testActorRef]);
  const handleCloseTestResultModal = useCallback(() => {
    testActorRef?.send({ type: "user.closeTestResultModal" });
  }, [testActorRef]);
  const handleSelectTest = useCallback((data: Test) => {
    testActorRef?.send({ type: "user.selectTest", data });
  }, [testActorRef]);

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
        testResult: handleSelectSingleTestResult
      },
      close: {
        testResultModal: handleCloseTestResultModal
      }
    }
  }
}

export type TestData = ReturnType<typeof useTestContext>["data"];
export type TestActions = ReturnType<typeof useTestContext>["actions"];
