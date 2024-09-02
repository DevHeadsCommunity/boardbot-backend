import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { TestCase } from "@/types";
import { Product } from "@/types/Product";
import { UploadIcon } from "lucide-react";
import React, { useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

interface CreateTestCardProps {
  addTest: (data: { name: string; id: string; testCases: TestCase[]; createdAt: string }) => void;
}

interface FormData {
  testName: string;
  testType: "accuracy" | "consistency";
}

interface ConsistencyTestCase {
  prompt: string;
  variations: string[];
}

interface AccuracyTestCase {
  prompt: string;
  products: Product[];
}

const CreateTestCard: React.FC<CreateTestCardProps> = ({ addTest }) => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      testType: "accuracy",
    },
  });

  const testType = watch("testType");

  console.log("testType", testType);

  const validateTestCases = (testCases: any[]): string | null => {
    if (!Array.isArray(testCases) || testCases.length === 0) {
      return "Invalid test cases format";
    }

    if (testType === "consistency") {
      return validateConsistencyTestCases(testCases);
    } else {
      return validateAccuracyTestCases(testCases);
    }
  };

  const validateConsistencyTestCases = (testCases: ConsistencyTestCase[]): string | null => {
    for (let i = 0; i < testCases.length; i++) {
      const testCase = testCases[i];
      if (!testCase.prompt || !Array.isArray(testCase.variations) || testCase.variations.length < 5) {
        return `Invalid consistency test case at index ${i}`;
      }
    }
    return null;
  };

  const validateAccuracyTestCases = (testCases: AccuracyTestCase[]): string | null => {
    for (let i = 0; i < testCases.length; i++) {
      const testCase = testCases[i];
      if (!testCase.prompt || !Array.isArray(testCase.products) || testCase.products.length === 0) {
        return `Invalid accuracy test case at index ${i}`;
      }
    }
    return null;
  };

  const parseTestCases = (testCases: any[]): TestCase[] => {
    if (testType === "consistency") {
      return parseConsistencyTestCases(testCases);
    } else {
      return parseAccuracyTestCases(testCases);
    }
  };

  const parseConsistencyTestCases = (testCases: ConsistencyTestCase[]): TestCase[] => {
    return testCases.map((testCase) => ({
      messageId: uuidv4(),
      input: testCase.prompt,
      expectedProducts: [],
      testType: "consistency",
      consistencyPrompts: testCase.variations,
    }));
  };

  const parseAccuracyTestCases = (testCases: AccuracyTestCase[]): TestCase[] => {
    return testCases.map((testCase) => ({
      messageId: uuidv4(),
      input: testCase.prompt,
      expectedProducts: testCase.products,
      testType: "accuracy",
    }));
  };

  const onSubmit = async (data: FormData) => {
    if (!file) {
      toast.error("Please upload a test file.");
      return;
    }

    try {
      const fileContent = await file.text();
      const jsonData = JSON.parse(fileContent);

      const validationError = validateTestCases(jsonData);
      if (validationError) {
        toast.error(`Invalid JSON data: ${validationError}`);
        return;
      }

      const testCases = parseTestCases(jsonData);

      addTest({
        name: data.testName,
        id: uuidv4(),
        testCases: testCases,
        createdAt: new Date().toISOString(),
      });

      setFile(null);
      reset();
      toast.success("Test created successfully");
    } catch (error) {
      toast.error(`Failed to parse the JSON file: ${(error as Error).message}`);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "application/json") {
        toast.error("Please upload a JSON file.");
        return;
      }
      setFile(selectedFile);
    }
  };

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold">Create Test</h2>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="testName" className="mb-1 block text-sm font-medium text-muted-foreground">
              Test Name
            </label>
            <Input id="testName" {...register("testName", { required: "Test name is required" })} placeholder="Enter test name" />
            {errors.testName && <p className="mt-1 text-sm text-red-500">{errors.testName.message}</p>}
          </div>
          <div>
            <label htmlFor="testType" className="mb-1 block text-sm font-medium text-muted-foreground">
              Test Type
            </label>
            <Controller
              name="testType"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select test type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accuracy">Accuracy</SelectItem>
                    <SelectItem value="consistency">Consistency</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div>
            <p className="mb-1 text-sm font-medium text-muted-foreground">Upload the test document (JSON)</p>
            <div
              className="flex flex-1 cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-muted p-6 text-muted-foreground transition-colors hover:border-primary-foreground"
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
              aria-label="Upload test file"
            >
              <UploadIcon className="mb-2 h-8 w-8" />
              <p>{file ? file.name : "Click or drag file to upload"}</p>
            </div>
            <input ref={fileInputRef} type="file" accept=".json" onChange={handleFileChange} className="hidden" />
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" variant="default" className="w-full">
            Create Test
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default CreateTestCard;
