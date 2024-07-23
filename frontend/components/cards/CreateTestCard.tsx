import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { TestCase } from "@/types";
import { Product } from "@/types/Product";
import { UploadIcon } from "lucide-react";
import Papa from "papaparse";
import React, { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

interface CreateTestCardProps {
  addTest: (data: { name: string; id: string; testCase: TestCase[]; createdAt: string }) => void;
}

interface FormData {
  testName: string;
}

interface CSVRow {
  prompt: string;
  name: string;
  size: string;
  form: string;
  processor: string;
  memory: string;
  io: string;
  manufacturer: string;
  summary: string;
}

const CreateTestCard: React.FC<CreateTestCardProps> = ({ addTest }) => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>();

  const validateCSVData = (data: CSVRow[]): string | null => {
    const requiredFields = ["prompt", "name", "size", "form", "processor", "memory", "io", "manufacturer", "summary"];

    for (let i = 0; i < data.length; i++) {
      const row = data[i];
      for (const field of requiredFields) {
        if (!row[field as keyof CSVRow]) {
          return `Row ${i + 1}: Missing ${field}`;
        }
      }
    }

    return null;
  };

  const onSubmit = async (data: FormData) => {
    if (!file) {
      toast.error("Please upload a test file.");
      return;
    }

    Papa.parse(file, {
      complete: (results) => {
        const csvData = results.data as CSVRow[];
        const validationError = validateCSVData(csvData);

        if (validationError) {
          toast.error(`Invalid CSV data: ${validationError}`);
          return;
        }

        const testCasesMap = new Map<string, TestCase>();

        csvData.forEach((row) => {
          const product: Product = {
            name: row.name,
            size: row.size,
            form: row.form,
            processor: row.processor,
            memory: row.memory,
            io: row.io,
            manufacturer: row.manufacturer,
            summary: row.summary,
            processorTDP: "0",
            operatingSystem: "0",
            environmental: "0",
            certifications: "0",
          };

          if (testCasesMap.has(row.prompt)) {
            testCasesMap.get(row.prompt)!.expectedProducts.push(product);
          } else {
            testCasesMap.set(row.prompt, {
              messageId: uuidv4(),
              input: row.prompt,
              expectedProducts: [product],
            });
          }
        });

        const testCases = Array.from(testCasesMap.values());

        addTest({
          name: data.testName,
          id: uuidv4(),
          testCase: testCases,
          createdAt: new Date().toISOString(),
        });

        setFile(null);
        reset();
      },
      header: true,
      skipEmptyLines: true,
      error: (error) => {
        toast.error(`Failed to parse the CSV file: ${error.message}`);
      },
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type !== "text/csv") {
        toast.error("Please upload a CSV file.");
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
            <p className="mb-1 text-sm font-medium text-muted-foreground">Upload the test document (CSV)</p>
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
            <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
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
