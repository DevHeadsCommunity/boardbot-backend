import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Test, TestCase } from "@/types";
import { UploadIcon } from "lucide-react";
import React, { ChangeEvent, useCallback, useRef, useState } from "react";
import { toast, ToastOptions } from "react-toastify";
import { v4 as uuidv4 } from "uuid";

export type ToastType = "success" | "error" | "info" | "warning";

interface CreateTestCardProps {
  addTest: (test: Test) => void;
}

const CreateTestCard: React.FC<CreateTestCardProps> = ({ addTest }) => {
  const [testName, setTestName] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = useCallback((type: ToastType, message: string) => {
    const toastOptions: ToastOptions = {
      position: "bottom-right",
      autoClose: 3000,
      hideProgressBar: false,
      closeOnClick: false,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
      type,
    };
    toast(message, toastOptions);
  }, []);

  const handleTestNameChange = (e: ChangeEvent<HTMLInputElement>) => {
    setTestName(e.target.value);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "application/json") {
        showToast("error", "Please upload a JSON file.");
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type !== "application/json") {
        showToast("error", "Please upload a JSON file.");
        return;
      }
      setFile(droppedFile);
    }
  };

  const handleCreate = async () => {
    if (!testName.trim()) {
      showToast("error", "Please enter a test name.");
      return;
    }

    if (!file) {
      showToast("error", "Please upload a test file.");
      return;
    }

    try {
      const fileContent = await file.text();
      const testData = JSON.parse(fileContent) as Partial<TestCase>[];

      if (!Array.isArray(testData)) {
        throw new Error("Invalid test data format. Expected an array.");
      }

      const testCases: TestCase[] = testData.map((testCase) => ({
        id: uuidv4(),
        input: testCase.input || "",
        expectedOutput: testCase.expectedOutput || "",
      }));
      console.log(`Test cases: ${testCases}`);

      const test: Test = {
        id: uuidv4(),
        name: testName,
        testCases,
        status: "PENDING",
      };

      console.log(`Test: ${test}`);

      addTest(test);
      setTestName("");
      setFile(null);
      showToast("success", "Test created successfully.");
    } catch (error) {
      showToast(
        "error",
        `Failed to parse the test file: ${(error as Error).message}`
      );
    }
  };

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold">Create Test</h2>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label
            htmlFor="testName"
            className="block text-sm font-medium text-muted-foreground mb-1"
          >
            Test Name
          </label>
          <Input
            id="testName"
            type="text"
            placeholder="Enter test name"
            value={testName}
            onChange={handleTestNameChange}
          />
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground mb-1">
            Upload the test document
          </p>
          <div
            className="flex-1 border-2 border-dashed border-muted rounded-md flex flex-col items-center justify-center p-6 text-muted-foreground hover:border-primary-foreground transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            role="button"
            tabIndex={0}
            aria-label="Upload test file"
          >
            <UploadIcon className="w-8 h-8 mb-2" />
            <p>{file ? file.name : "Click or drag file to upload"}</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={handleCreate} variant="default" className="w-full">
          Create Test
        </Button>
      </CardFooter>
    </Card>
  );
};

export default CreateTestCard;
