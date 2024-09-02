import { TestCase } from "@/types";
import { useSelector } from "@xstate/react";
import { useCallback, useMemo } from "react";
import { useAppContext } from "./useAppContext";
import { useToast } from "./useToast";

export enum TestState {
  Idle = "Idle",
  DisplayingTest = "DisplayingTest",
  DisplayingTestPage = "DisplayingTestPage",
  DisplayingSelectedTest = "DisplayingSelectedTest",
  DisplayingTestDetailsModal = "DisplayingTestDetailsModal",
}

const stateMap: Record<string, TestState> = {
  idle: TestState.Idle,
  displayingTest: TestState.DisplayingTest,
  "displayingTest.displayingTestPage": TestState.DisplayingTestPage,
  "displayingTest.displayingTestDetails.displayingSelectedTest": TestState.DisplayingSelectedTest,
  "displayingTest.displayingTestDetails.displayingTestDetailsModal": TestState.DisplayingTestDetailsModal,
};

type TestAction =
  | { type: "app.startTest" }
  | { type: "app.stopTest" }
  | { type: "user.createTest"; data: { testType: string; name: string; id: string; testCase: TestCase[]; createdAt: string } }
  | { type: "user.selectTest"; data: { testId: string } }
  | { type: "user.clickSingleTestResult" }
  | { type: "user.closeTestResultModal" };

export const useTestContext = () => {
  const { actorRef } = useAppContext();
  const testActorRef = actorRef.test;
  const testActorState = useSelector(testActorRef, (state) => state);
  useToast(testActorRef);

  const testState = useMemo(() => {
    if (!testActorState) return TestState.Idle;
    const currentState = testActorState.value as string;
    return stateMap[currentState] || TestState.Idle;
  }, [testActorState]);

  const testDispatch = useCallback(
    (action: TestAction) => {
      testActorRef?.send(action);
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
      select: {
        startTest: () => testDispatch({ type: "app.startTest" }),
        stopTest: () => testDispatch({ type: "app.stopTest" }),
        test: (testId: string) => testDispatch({ type: "user.selectTest", data: { testId } }),
        testResult: () => testDispatch({ type: "user.clickSingleTestResult" }),
      },
      submit: {
        createTest: (data: { testType: string; name: string; id: string; testCase: TestCase[]; createdAt: string }) => testDispatch({ type: "user.createTest", data }),
      },
      close: {
        testResultModal: () => testDispatch({ type: "user.closeTestResultModal" }),
      },
    },
  };
};

export type TestData = ReturnType<typeof useTestContext>["data"];
export type TestActions = ReturnType<typeof useTestContext>["actions"];
