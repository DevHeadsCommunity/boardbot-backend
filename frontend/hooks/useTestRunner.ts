import useWebSocket from "@/hooks/useWebSocket";
import { Test, TestCase, TestResult, TestStatus } from "@/types";
import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

interface UseTestRunnerProps {
  test?: Test;
  batchSize?: number;
  testTimeout?: number;
}

const useTestRunner = ({
  test,
  batchSize = 5,
  testTimeout = 10000,
}: UseTestRunnerProps) => {
  const { sendTextMessage, chatHistory } = useWebSocket();
  const [currentTestIndex, setCurrentTestIndex] = useState(0);
  const [status, setStatus] = useState<TestStatus>(test?.status || "PENDING");
  const [progress, setProgress] = useState(0);
  const [currentTest, setCurrentTest] = useState<Test | undefined>(test);

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const processedMessageIds = useRef<Set<string>>(new Set());

  const handleTestResult = useCallback(
    (testCase: TestCase, output: string, error?: Error) => {
      if (currentTest === undefined) return;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      const responseTime = startTimeRef.current
        ? Date.now() - startTimeRef.current
        : 0;

      const result: TestResult = {
        ...testCase,
        actualOutput: output,
        isCorrect: testCase.expectedOutput === output && !error,
        accuracyScore: testCase.expectedOutput === output ? 1 : 0,
        inputTokenCount: testCase.input.split(/\s+/).length,
        outputTokenCount: output.split(/\s+/).length,
        llmResponseTime: responseTime,
        backendProcessingTime: responseTime, // Assuming backend processing time is the same as response time
        totalResponseTime: responseTime,
        error: error?.message,
      };

      setCurrentTest((prev) => ({
        ...prev!,
        results: [...(prev?.results || []), result],
      }));

      setCurrentTestIndex((prev) => prev + 1);
      setProgress(
        ((currentTestIndex + 1) / currentTest.testCases.length) * 100
      );
    },
    [currentTest, currentTestIndex]
  );

  const runNextBatch = useCallback(() => {
    if (status !== "RUNNING") return;
    if (currentTest === undefined) return;

    const endIndex = Math.min(
      currentTestIndex + batchSize,
      currentTest.testCases.length
    );

    for (let i = currentTestIndex; i < endIndex; i++) {
      const testCase = currentTest.testCases[i];
      try {
        const messageId = uuidv4();
        sendTextMessage(messageId, testCase.input);
        startTimeRef.current = Date.now();
        timeoutRef.current = setTimeout(() => {
          handleTestResult(testCase, "", new Error("Test timed out"));
        }, testTimeout);
      } catch (error) {
        handleTestResult(
          testCase,
          "",
          error instanceof Error ? error : new Error("Unknown error")
        );
      }
    }
  }, [
    batchSize,
    currentTestIndex,
    handleTestResult,
    sendTextMessage,
    status,
    currentTest,
    testTimeout,
  ]);

  useEffect(() => {
    if (currentTest === undefined) return;
    if (
      currentTestIndex < currentTest.testCases.length &&
      status === "RUNNING"
    ) {
      runNextBatch();
    } else if (currentTestIndex >= currentTest.testCases.length) {
      setStatus("COMPLETED");
    }
  }, [currentTestIndex, currentTest, status, runNextBatch]);

  useEffect(() => {
    if (currentTest === undefined) return;
    const lastMessage = chatHistory[chatHistory.length - 1];
    if (
      lastMessage &&
      !lastMessage.isUserMessage &&
      !processedMessageIds.current.has(lastMessage.id)
    ) {
      processedMessageIds.current.add(lastMessage.id);
      const testCase = currentTest.testCases[currentTestIndex - 1];
      if (testCase) {
        handleTestResult(testCase, lastMessage.message);
      }
    }
  }, [chatHistory, currentTestIndex, currentTest, handleTestResult]);

  const startTest = useCallback(() => {
    setStatus("RUNNING");
    setCurrentTestIndex(0);
    setProgress(0);
    setCurrentTest({ ...currentTest!, results: [] });
  }, [currentTest]);

  const pauseTest = useCallback(() => setStatus("PAUSED"), []);

  const resumeTest = useCallback(() => setStatus("RUNNING"), []);

  const retryFailedTests = useCallback(() => {
    if (currentTest === undefined) return;

    const failedTests =
      currentTest.results?.filter((result) => !result.isCorrect) || [];
    if (failedTests.length > 0) {
      setStatus("RUNNING");
      setCurrentTest((prev) => ({
        ...prev!,
        results: prev?.results?.filter((result) => result.isCorrect) || [],
      }));
      setCurrentTestIndex((prev) => prev - failedTests.length);
    }
  }, [currentTest]);

  return {
    status,
    currentTest,
    progress,
    startTest,
    pauseTest,
    resumeTest,
    retryFailedTests,
  };
};

export default useTestRunner;
