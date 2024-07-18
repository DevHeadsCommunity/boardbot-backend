import { AppContext } from "@/context/appContext";
import { useSelector } from "@xstate/react";
import { useEffect, useState } from "react";
import { useToast } from "./useToast";


export const useTestContext = () => {
  const state = AppContext.useSelector((state) => state);
  const testActorRef = AppContext.useActorRef();
  useToast(testActorRef);
  const tests = useSelector(testActorRef, (state: any) => state.context.tests || []);
  const selectedTest = useSelector(testActorRef, (state: any) => state.context.selectedTest || null);
  const testActorState = useSelector(testActorRef, (state: any) => state);
  const [testState, setTestState] = useState<"Idle" | "DisplayingTest" | "DisplayingTestPage"| "DisplayingSelectedTest" | "DisplayingTestDetailsModal" | "RunningTest" >("Idle");

  useEffect(() => {
    if (testActorState.matches("Idle" as any)) {
      setTestState("Idle");
    } else if (testActorState.matches("DisplayingTest")) {
      setTestState("DisplayingTest");
    } else if (testActorState.matches("DisplayingTest.Connected.DisplayingTestPage" as any)) {
      setTestState("DisplayingTestPage");
    } else if (testActorState.matches("DisplayingTest.Connected.DisplayingTestDetails.DisplayingSelectedTest" as any)) {
      setTestState("DisplayingSelectedTest");
    } else if (testActorState.matches("DisplayingTest.Connected.DisplayingTestDetails.DisplayingTestDetailsModal" as any)) {
      setTestState("DisplayingTestDetailsModal");
    } else if (testActorState.matches("DisplayingTest.Connected.DisplayingTestDetails.RunningTest" as any)) {
      setTestState("RunningTest");
    }
  }
  , [testActorState]);

  const handleStartTest = () => {
    testActorRef.send({ type: "app.startTest" });
  };
  const handleStopTest = () => {
    testActorRef.send({ type: "app.stopTest" });
  };
  const handleCreateTest = () => {
    testActorRef.send({ type: "user.createTest" });
  };
  const handleRunTest = () => {
    testActorRef.send({ type: "user.runTest" });
  };
  const handlePauseTest = () => {
    testActorRef.send({ type: "user.pauseTest" });
  };
  const handleResumeTest = () => {
    testActorRef.send({ type: "user.resumeTest" });
  };
  const handleClickSingleTestResult = () => {
    testActorRef.send({ type: "user.clickSingleTestResult" });
  };
  const handleCloseTestResultModal = () => {
    testActorRef.send({ type: "user.closeTestResultModal" });
  };
  const handleSelectTest = (test: any) => {
    testActorRef.send({ type: "user.selectTest", data: test });
  };

  return {
    data: {
      tests,
      selectedTest,
      testState,
    },
    actions: {
      handleStartTest,
      handleStopTest,
      handleCreateTest,
      handleRunTest,
      handlePauseTest,
      handleResumeTest,
      handleClickSingleTestResult,
      handleCloseTestResultModal,
      handleSelectTest,
    }
  }
}

export type TestData = ReturnType<typeof useTestContext>["data"];
export type TestActions = ReturnType<typeof useTestContext>["actions"];
