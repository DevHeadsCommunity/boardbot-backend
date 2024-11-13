import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { useTestContext } from "@/hooks/useTestContext";
import { TEST_TYPES, TestCaseSchema } from "@/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { UploadIcon } from "lucide-react";
import React, { useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";
import { z } from "zod";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";

const formSchema = z.object({
  testName: z.string().min(1, "Test name is required"),
  testType: z.enum(TEST_TYPES),
});

type FormData = z.infer<typeof formSchema>;

const CreateTestCard: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { actions } = useTestContext();

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      testType: "accuracy",
    },
  });

  const validateTestCases = (testCases: unknown[], testType: string): z.ZodError | null => {
    let schema = z.array(TestCaseSchema);

    if (["context_retention", "conversational_flow", "defensibility"].includes(testType)) {
      schema = z.array(
        TestCaseSchema.extend({
          prompt: z.string().optional(),
          conversation: z
            .array(
              z.object({
                turn: z.number(),
                query: z.string(),
                expected_filters: z.record(z.any()).optional(),
                message: z.string().optional(),
              })
            )
            .min(2, "Conversation-based tests must include at least 2 turns"),
        }).transform((data) => ({
          ...data,
          prompt: data.prompt || data.conversation?.[0]?.query || "",
          messageId: data.messageId || uuidv4(),
        }))
      );
    }

    try {
      const validatedCases = schema.parse(testCases);
      return null;
    } catch (error) {
      if (error instanceof z.ZodError) {
        console.log("Validation errors:", error.errors);
        return error;
      }
      throw error;
    }
  };

  const validateContextRetention = (testCases: TestCase[]) => {
    for (const testCase of testCases) {
      if (!testCase.conversation) {
        throw new Error("Context retention tests must include conversation turns");
      }

      for (const turn of testCase.conversation) {
        if (!turn.query) {
          throw new Error("Each conversation turn must include a query");
        }
        if (!turn.expected_filters) {
          throw new Error("Context retention tests must include expected filters for each turn");
        }
      }
    }
  };

  const validateConversationalFlow = (testCases: TestCase[]) => {
    for (const testCase of testCases) {
      if (!testCase.conversation) {
        throw new Error("Conversational flow tests must include conversation turns");
      }

      for (const turn of testCase.conversation) {
        if (!turn.query) {
          throw new Error("Each conversation turn must include a query");
        }
      }
    }
  };

  const validateDefensibility = (testCases: TestCase[]) => {
    for (const testCase of testCases) {
      if (!testCase.conversation) {
        throw new Error("Defensibility tests must include conversation turns");
      }

      for (const turn of testCase.conversation) {
        if (!turn.query) {
          throw new Error("Each conversation turn must include a query");
        }
        if (!turn.message) {
          throw new Error("Defensibility tests must include expected responses for each turn");
        }
      }
    }
  };

  const onSubmit = async (data: FormData) => {
    if (!file) {
      toast.error("Please upload a test file.");
      return;
    }

    try {
      const fileContent = await file.text();
      const jsonData = JSON.parse(fileContent);

      // Transform test cases based on type
      const transformedData = jsonData.map((testCase: any) => {
        const baseCase = {
          ...testCase,
          messageId: testCase.messageId || uuidv4(),
          testType: data.testType,
        };

        if (["context_retention", "conversational_flow", "defensibility"].includes(data.testType)) {
          return {
            ...baseCase,
            prompt: testCase.prompt || testCase.conversation?.[0]?.query || "",
          };
        }

        return baseCase;
      });

      const validationError = validateTestCases(transformedData, data.testType);
      if (validationError) {
        const errorMessages = validationError.errors.map((err) => `${err.path.join(".")} - ${err.message}`).join("\n");
        toast.error(`Invalid JSON data:\n${errorMessages}`, { autoClose: false });
        return;
      }

      actions.submit.createTest({
        testType: data.testType,
        name: data.testName,
        id: uuidv4(),
        testCase: transformedData,
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
            <Input id="testName" {...register("testName")} placeholder="Enter test name" />
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
                    {TEST_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type.replace("_", " ").replace(/^\w/, (c) => c.toUpperCase())}
                      </SelectItem>
                    ))}
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
