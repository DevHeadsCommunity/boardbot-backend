import useWebSocket from "@/hooks/useWebSocket";
import { Product, Test, TestCase, TestResult, TestStatus } from "@/types";
import { useCallback, useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { ChatMessage } from "./useConsumer";

interface UseTestRunnerProps {
  test: Test;
  batchSize?: number;
  testTimeout?: number;
}

interface RunningTestCase {
  testCase: TestCase;
  messageId: string;
}

const useTestRunner = ({
  test,
  batchSize = 5,
  testTimeout = 180000, // 3 minutes
}: UseTestRunnerProps) => {
  const { sendTextMessage, chatHistory } = useWebSocket();
  const [currentTestIndex, setCurrentTestIndex] = useState(0);
  const [status, setStatus] = useState<TestStatus>(test?.status || "PENDING");
  const [progress, setProgress] = useState(0);
  const [currentTest, setCurrentTest] = useState<Test>(test);

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const runningTestCase = useRef<RunningTestCase | null>(null);

  // Utility functions
  const compareProducts = useCallback(
    (expected: Product[], actual: Product[]): boolean => {
      if (expected.length !== actual.length) return false;
      return expected.every(
        (expectedProduct, index) =>
          JSON.stringify(expectedProduct) === JSON.stringify(actual[index])
      );
    },
    []
  );

  const calculateAccuracy = useCallback(
    (expected: Product[], actual: Product[]): number => {
      if (expected.length === 0) return 0;
      const correctProducts = expected.filter(
        (expectedProduct, index) =>
          JSON.stringify(expectedProduct) === JSON.stringify(actual[index])
      );
      return correctProducts.length / expected.length;
    },
    []
  );

  const extractFeatures = useCallback((product: Product): (string | "NA")[] => {
    return [
      product.manufacturer || "NA",
      product.form || "NA",
      product.processor || "NA",
      product.processorTDP || "NA",
      product.memory || "NA",
      product.io || "NA",
      product.operatingSystem || "NA",
      product.environmental || "NA",
      product.certifications || "NA",
    ];
  }, []);

  const calculateFeatureAccuracy = useCallback(
    (expected: Product[], actual: Product[]): number => {
      // const expectedFeatures = expected.flatMap(extractFeatures);
      // const actualFeatures = actual.flatMap(extractFeatures);

      // const nonNACount = expectedFeatures.filter(
      //   (feature) => feature !== "NA"
      // ).length;
      // const correctlyExtractedCount = expectedFeatures.filter(
      //   (feature, index) =>
      //     feature !== "NA" && feature === actualFeatures[index]
      // ).length;

      // return nonNACount > 0 ? correctlyExtractedCount / nonNACount : 0;
      return 1;
    },
    [extractFeatures]
  );

  // Core logic
  const handleTestResult = useCallback(
    (testCase: TestCase, resMessage: ChatMessage, error?: Error) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      console.log("Received output:", resMessage.message);

      const responseTime = startTimeRef.current
        ? Date.now() - startTimeRef.current
        : 0;

      let parsedOutput: Product[] = [];
      let isCorrect = false;
      let productAccuracy = 0;
      let featureAccuracy = 0;

      try {
        parsedOutput = JSON.parse(resMessage.message) as Product[];
        isCorrect = compareProducts(testCase.expectedProducts, parsedOutput);
        productAccuracy = calculateAccuracy(
          testCase.expectedProducts,
          parsedOutput
        );
        featureAccuracy = calculateFeatureAccuracy(
          testCase.expectedProducts,
          parsedOutput
        );
      } catch (parseError) {
        console.error("Failed to parse output:", parseError);
      }

      const result: TestResult = {
        ...testCase,
        actualOutput: resMessage.message,
        isCorrect,
        productAccuracy,
        featureAccuracy,
        inputTokenCount: resMessage.inputTokenCount!,
        outputTokenCount: resMessage.outputTokenCount!,
        llmResponseTime: resMessage.elapsedTime!,
        backendProcessingTime: responseTime,
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

      runningTestCase.current = null;
    },
    [
      currentTest,
      currentTestIndex,
      compareProducts,
      calculateAccuracy,
      calculateFeatureAccuracy,
    ]
  );

  const runNextTestCase = useCallback(() => {
    if (status !== "RUNNING") return;
    if (currentTestIndex >= currentTest.testCases.length) {
      setStatus("COMPLETED");
      return;
    }

    const testCase = currentTest.testCases[currentTestIndex];
    const messageId = uuidv4();
    runningTestCase.current = { testCase, messageId };

    try {
      sendTextMessage(messageId, testCase.input);
      console.log("Sent message:", testCase.input);
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
  }, [
    status,
    currentTest,
    currentTestIndex,
    sendTextMessage,
    handleTestResult,
    testTimeout,
  ]);

  // Effects
  useEffect(() => {
    if (status === "RUNNING" && runningTestCase.current === null) {
      runNextTestCase();
    }
  }, [status, runningTestCase, runNextTestCase]);

  useEffect(() => {
    if (currentTest === undefined || runningTestCase.current === null) return;

    const lastMessage = chatHistory[chatHistory.length - 1];
    if (
      lastMessage &&
      !lastMessage.isUserMessage &&
      lastMessage.id.replace(/_response$/, "") ===
        runningTestCase.current.messageId
    ) {
      handleTestResult(runningTestCase.current.testCase, lastMessage);
    }
  }, [chatHistory, handleTestResult, currentTest]);

  // Public methods
  const startTest = useCallback(() => {
    setStatus("RUNNING");
    setCurrentTestIndex(0);
    setProgress(0);
    setCurrentTest({ ...currentTest!, results: [] });
    runningTestCase.current = null;
  }, [currentTest]);

  const pauseTest = useCallback(() => {
    setStatus("PAUSED");
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

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
      runningTestCase.current = null;
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
