import { FullTestResult, TestCase, TestResult } from "@/types";
import { setup } from "xstate";

export const testRunnerMachine = setup({
  types: {
    context: {} as {
      testCases: TestCase[];
      testResults: TestResult[];
      FullTestResult: FullTestResult| null;
      currentTestIndex: number;
      batchSize: number;
      testTimeout: number;
    },
    events: {} as
    | { type: "test.startTest" }
    | { type: "test.continueTest" }
    | { type: "test.pauseTest" }
      | { type: "test.stopTest" },
  },
  actors: {
    testRunner: createMachine({
      /* ... */
    }),
    testEvaluator: createMachine({
      /* ... */
    }),
    fullTestEvaluator: createMachine({
      /* ... */
    }),
  },
  guards: {
    testIsComplete: function ({ context, event }) {
      // Add your guard condition here
      return true;
    },
  },
}).createMachine({
  context: {
    testCases: [],
    testResults: [],
    FullTestResult: null,
    currentTestIndex: 0,
    batchSize: 5,
    testTimeout: 180000,
  },
  id: "testRunnerActor",
  initial: "idle",
  states: {
    idle: {
      on: {
        "test.startTest": {
          target: "RunningTest",
        },
      },
    },
    RunningTest: {
      initial: "RunningBatchTest",
      on: {
        "test.pauseTest": {
          target: "TestPaused",
        },
        "test.stopTest": {
          target: "idle",
        },
      },
      states: {
        RunningBatchTest: {
          invoke: {
            id: "testRunner",
            input: {},
            onDone: {
              target: "EvaluateBatchResult",
            },
            src: "testRunner",
          },
        },
        EvaluateBatchResult: {
          invoke: {
            id: "testEvaluator",
            input: {},
            onDone: [
              {
                target: "#testRunnerActor.TestCompleted",
                guard: {
                  type: "testIsComplete",
                },
              },
              {
                target: "RunningBatchTest",
              },
            ],
            src: "testEvaluator",
          },
        },
        Continue: {
          type: "history",
          history: "shallow",
        },
      },
    },
    TestPaused: {
      on: {
        "test.continueTest": {
          target: "#testRunnerActor.RunningTest.Continue",
        },
      },
    },
    TestCompleted: {
      invoke: {
        id: "fullTestEvaluator",
        input: {},
        src: "fullTestEvaluator.ts",
      },
    },
  },
});
