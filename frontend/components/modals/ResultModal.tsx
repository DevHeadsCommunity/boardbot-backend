import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { getScoreColor } from "@/lib/utils/scores";
import { TestCase } from "@/types";
import React from "react";
import ChatMessageContent from "../blocks/ChatMessageContent";
import CopyButton from "../blocks/CopyButton";
import { TransformedData } from "../cards/TestResultCard";

interface ResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TransformedData;
  testCase: TestCase | undefined;
}

const ResultModal: React.FC<ResultModalProps> = ({ isOpen, onClose, data, testCase }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl">
        <DialogHeader>
          <DialogTitle>Test Result Details</DialogTitle>
          <div className="mt-2 text-sm text-muted-foreground">{testCase?.description}</div>
        </DialogHeader>
        <ScrollArea className="max-h-[80vh] overflow-y-auto">
          <div className="space-y-6 p-4">
            <GeneralInformation data={data} />
            <Metrics data={data} />
            <TestInput testCase={testCase} />
            {data.testType === "accuracy" && <AccuracyResultDetails data={data} testCase={testCase} />}
            {data.testType === "consistency" && <ConsistencyResultDetails data={data} testCase={testCase} />}
            {data.testType === "feature_inference" && <FeatureInferenceResultDetails data={data} testCase={testCase} />}
            {data.testType === "context_retention" && <ContextRetentionResultDetails data={data} testCase={testCase} />}
            {data.testType === "conversational_flow" && <ConversationalFlowResultDetails data={data} testCase={testCase} />}
            {data.testType === "robustness" && <RobustnessResultDetails data={data} testCase={testCase} />}
            {data.testType === "defensibility" && <DefensibilityResultDetails data={data} testCase={testCase} />}
          </div>
        </ScrollArea>
        <DialogFooter>
          <Button onClick={onClose} variant="outline">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const GeneralInformation: React.FC<{ data: TransformedData }> = ({ data }) => (
  <Card className="bg-muted p-4">
    <h3 className="mb-2 text-lg font-semibold">General Information</h3>
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <MetricItem label="Test Type" value={data.testType} />
      <MetricItem label="Model" value={data.model} />
      <MetricItem label="Architecture" value={data.architectureChoice} />
      <MetricItem label="History Management" value={data.historyManagementChoice} />
      <MetricItem label="Timestamp" value={data.timestamp.toLocaleString()} />
    </div>
  </Card>
);

const Metrics: React.FC<{ data: TransformedData }> = ({ data }) => (
  <Card className="bg-muted p-4">
    <h3 className="mb-2 text-lg font-semibold">Metrics</h3>
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {data.testType === "robustness" ? (
        <>
          <MetricItem label="Filter Accuracy" value={`${(data.filterAccuracy! * 100).toFixed(2)}%`} />
          <MetricItem label="Noise Filtering" value={`${(data.noiseFiltering! * 100).toFixed(2)}%`} />
        </>
      ) : data.testType === "accuracy" ? (
        <MetricItem label="Product Accuracy" value={`${(data.productAccuracy! * 100).toFixed(2)}%`} />
      ) : data.testType === "consistency" ? (
        <>
          <MetricItem label="Product Consistency" value={`${(data.productConsistency! * 100).toFixed(2)}%`} />
          <MetricItem label="Order Consistency" value={`${(data.orderConsistency! * 100).toFixed(2)}%`} />
        </>
      ) : data.testType === "feature_inference" ? (
        <MetricItem label="Filter Accuracy" value={`${(data.filterAccuracy! * 100).toFixed(2)}%`} />
      ) : data.testType === "context_retention" ? (
        <MetricItem label="Context Accuracy" value={`${(data.contextAccuracy! * 100).toFixed(2)}%`} />
      ) : data.testType === "conversational_flow" ? (
        <MetricItem label="Flow Coherence" value={`${(data.flowCoherence! * 100).toFixed(2)}%`} />
      ) : data.testType === "robustness" ? (
        <MetricItem label="Filter Accuracy" value={`${(data.filterAccuracy! * 100).toFixed(2)}%`} />
      ) : data.testType === "defensibility" ? (
        <MetricItem label="Boundary Maintenance" value={`${(data.boundaryMaintenance! * 100).toFixed(2)}%`} />
      ) : null}
    </div>
  </Card>
);

const TestInput: React.FC<{ testCase: TestCase | undefined }> = ({ testCase }) => (
  <Card className="bg-muted p-4">
    <h3 className="mb-2 text-lg font-semibold">Test Input</h3>
    <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{testCase?.prompt}</pre>
  </Card>
);

const AccuracyResultDetails: React.FC<{ data: TransformedData; testCase: TestCase | undefined }> = ({ data, testCase }) => {
  const copyToClipboard = () => {
    const jsonData = JSON.stringify(
      {
        prompt: testCase?.prompt || "",
        filters: data.metadata?.filters,
        expectedProducts: testCase?.products,
        actualProducts: data.products,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  return (
    <>
      <div className="flex justify-end">
        <CopyButton onClick={copyToClipboard} />
      </div>
      <Card className="bg-muted p-4">
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-lg font-semibold">Filters</h4>
            <FilterList filters={data.metadata?.filters} />
          </div>
        </div>
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Expected Products</h3>
        <ChatMessageContent message={JSON.stringify(testCase?.products, null, 2)} />
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Actual Products</h3>
        <ChatMessageContent message={JSON.stringify(data.products, null, 2)} />
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Response</h3>
        <ChatMessageContent message={data.response} />
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
        <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
      </Card>
    </>
  );
};

const ConsistencyResultDetails: React.FC<{ data: TransformedData; testCase: TestCase | undefined }> = ({ data, testCase }) => {
  const copyToClipboard = (prompt: string, filters: Record<string, string> | undefined, products: string[]) => {
    const jsonData = JSON.stringify(
      {
        prompt,
        filters,
        products,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  const copyFullTest = () => {
    const fullTestData = {
      mainPrompt: {
        prompt: testCase?.prompt || "",
        filters: data.metadata?.filters,
        products: data.products.map((p) => p.name),
      },
      variations: data.variationResponses?.map((variation, index) => ({
        prompt: testCase?.variations?.[index] || "",
        filters: variation.metadata?.filters,
        products: variation.products.map((p) => p.name),
      })),
    };
    navigator.clipboard.writeText(JSON.stringify(fullTestData, null, 2));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <CopyButton onClick={copyFullTest} />
      </div>
      <Card className="relative bg-muted p-6">
        <CopyButton
          onClick={() =>
            copyToClipboard(
              testCase?.prompt || "",
              data.metadata?.filters,
              data.products.map((p) => p.name)
            )
          }
        />
        <h3 className="mb-4 text-xl font-semibold">Main Prompt Response</h3>
        <div className="mb-2">
          <Badge variant="secondary">Result Type: {data.responseType}</Badge>
        </div>
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <p className="text-gray-700">{data.response}</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-lg font-semibold">Products</h4>
            <ProductList products={data.products.map((p) => p.name)} />
          </div>
          <div>
            <h4 className="mb-2 text-lg font-semibold">Filters</h4>
            <FilterList filters={data.metadata?.filters} />
          </div>
        </div>
        <Separator className="my-4" />
        <h4 className="mb-2 text-lg font-semibold">Reasoning</h4>
        <pre className="whitespace-pre-wrap break-words rounded-lg bg-gray-100 p-4 text-sm text-gray-800">{data.reasoning}</pre>
      </Card>
      {data.variationResponses?.map((variation, index) => (
        <Card key={index} className="relative bg-muted p-6">
          <CopyButton
            onClick={() =>
              copyToClipboard(
                testCase?.variations?.[index] || "",
                variation.metadata?.filters,
                variation.products.map((p) => p.name)
              )
            }
          />
          <h3 className="mb-4 text-xl font-semibold">Variation {index + 1}</h3>
          <div className="mb-2">
            <Badge variant="secondary">Result Type: {variation.type}</Badge>
          </div>
          <div className="mb-4">
            <h4 className="mb-2 text-lg font-semibold">Prompt</h4>
            <pre className="whitespace-pre-wrap break-words rounded-lg bg-gray-100 p-4 text-sm text-gray-800">{testCase?.variations?.[index]}</pre>
          </div>
          <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
            <h4 className="mb-2 text-lg font-semibold">Response</h4>
            <p className="text-gray-700">{variation.response}</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h4 className="mb-2 text-lg font-semibold">Products</h4>
              <ProductList products={variation.products.map((p) => p.name)} />
            </div>
            <div>
              <h4 className="mb-2 text-lg font-semibold">Filters</h4>
              <FilterList filters={variation.metadata?.filters} />
            </div>
          </div>
          <Separator className="my-4" />
          <h4 className="mb-2 text-lg font-semibold">Reasoning</h4>
          <pre className="whitespace-pre-wrap break-words rounded-lg bg-gray-100 p-4 text-sm text-gray-800">{variation.reasoning}</pre>
        </Card>
      ))}
    </div>
  );
};

const MetricItem: React.FC<{ label: string; value: string | number | Date | undefined }> = ({ label, value }) => {
  if (value === undefined) return null;

  let displayValue = value;
  if (value instanceof Date) {
    displayValue = value.toLocaleString();
  }

  return (
    <div>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{displayValue}</p>
    </div>
  );
};

const ProductList: React.FC<{ products: string[] }> = ({ products }) => (
  <ul className="space-y-2">
    {products.map((product, index) => (
      <li key={index} className="flex items-center">
        <Badge variant="secondary" className="mr-2">
          {index + 1}
        </Badge>
        <span className="text-sm">{product}</span>
      </li>
    ))}
  </ul>
);

const FilterList: React.FC<{ filters: Record<string, string> | undefined }> = ({ filters }) => {
  if (!filters || Object.keys(filters).length === 0) {
    return <p className="text-sm italic text-gray-500">No filters applied</p>;
  }

  return (
    <ul className="space-y-2">
      {Object.entries(filters).map(([key, value]) => (
        <li key={key} className="flex items-center">
          <Badge className="mr-2">{key}</Badge>
          <span className="text-sm">{value}</span>
        </li>
      ))}
    </ul>
  );
};

const FeatureInferenceResultDetails: React.FC<{
  data: TransformedData;
  testCase: TestCase | undefined;
}> = ({ data, testCase }) => {
  const copyToClipboard = () => {
    const jsonData = JSON.stringify(
      {
        prompt: testCase?.prompt || "",
        expectedFilters: testCase?.expected_filters,
        extractedFilters: data.extractedFilters,
        filterAccuracy: data.filterAccuracy,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  return (
    <>
      <div className="flex justify-end">
        <CopyButton onClick={copyToClipboard} />
      </div>
      <Card className="bg-muted p-4">
        <h3 className="mb-4 text-lg font-semibold">Filter Comparison</h3>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-lg font-semibold">Expected Filters</h4>
            <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{JSON.stringify(testCase?.expected_filters, null, 2)}</pre>
          </div>
          <div>
            <h4 className="mb-2 text-lg font-semibold">Extracted Filters</h4>
            <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{JSON.stringify(data.extractedFilters, null, 2)}</pre>
          </div>
        </div>
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Response</h3>
        <ChatMessageContent message={data.response} />
      </Card>
      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
        <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
      </Card>
    </>
  );
};

const ContextRetentionResultDetails: React.FC<{
  data: TransformedData;
  testCase: TestCase | undefined;
}> = ({ data, testCase }) => {
  return (
    <>
      <div className="space-y-6">
        <Card className="bg-muted p-4">
          <h3 className="mb-4 text-lg font-semibold">Conversation History</h3>
          {data.conversation?.map((turn, index) => (
            <div key={index} className="mb-6">
              <div className="mb-2 flex items-center gap-2">
                <Badge>Turn {index + 1}</Badge>
                <Badge variant="outline">{turn === data.conversation![0] ? "Initial Query" : "Follow-up"}</Badge>
              </div>
              <div className="space-y-4 rounded-lg bg-white p-4 shadow-sm">
                <div>
                  <h4 className="mb-2 font-medium">Query</h4>
                  <p className="text-gray-700">{testCase?.conversation?.[index]?.query || "N/A"}</p>
                </div>
                <Separator />
                <div>
                  <h4 className="mb-2 font-medium">Response</h4>
                  <p className="text-gray-700">{turn.message.message}</p>
                </div>
                <div>
                  <h4 className="mb-2 font-medium">Filters</h4>
                  <FilterList filters={data.filterProgression?.[index]} />
                </div>
              </div>
            </div>
          ))}
        </Card>

        <Card className="bg-muted p-4">
          <h3 className="mb-4 text-lg font-semibold">Filter Progression</h3>
          <div className="space-y-4">
            {data.filterProgression?.map((filters, index) => (
              <div key={index}>
                <h4 className="mb-2 font-medium">Turn {index + 1}</h4>
                <FilterList filters={filters} />
                {index < (data.filterProgression?.length || 0) - 1 && (
                  <div className="my-2 flex items-center justify-center">
                    <span className="text-2xl">↓</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card className="bg-muted p-4">
          <h3 className="mb-2 text-lg font-semibold">Context Retention Score</h3>
          <div className={`text-2xl font-bold ${getScoreColor(data.contextAccuracy)}`}>{(data.contextAccuracy! * 100).toFixed(2)}%</div>
        </Card>
      </div>
    </>
  );
};

const ConversationalFlowResultDetails: React.FC<{
  data: TransformedData;
  testCase: TestCase | undefined;
}> = ({ data, testCase }) => {
  const copyToClipboard = () => {
    const jsonData = JSON.stringify(
      {
        conversation: data.conversation?.map((turn, index) => ({
          turn: index + 1,
          expectedFilters: testCase?.conversation?.[index]?.expected_filters,
          extractedFilters: turn.extractedFilters,
        })),
        flowCoherence: data.flowCoherence,
        topicTransitionAccuracy: data.topicTransitionAccuracy,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  return (
    <>
      <div className="flex justify-end">
        <CopyButton onClick={copyToClipboard} />
      </div>
      <div className="space-y-6">
        <Card className="bg-muted p-4">
          <h3 className="mb-4 text-lg font-semibold">Filter Progression Analysis</h3>
          {data.conversation?.map((turn, index) => (
            <div key={index} className="mb-6">
              <div className="mb-2 flex items-center gap-2">
                <Badge>Turn {index + 1}</Badge>
                <Badge variant="outline">{turn === data.conversation![0] ? "Initial Query" : "Follow-up"}</Badge>
              </div>
              <div className="space-y-4 rounded-lg bg-white p-4 shadow-sm">
                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <h4 className="mb-2 font-medium">Expected Filters</h4>
                    <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">
                      {JSON.stringify(testCase?.conversation?.[index]?.expected_filters, null, 2) || "N/A"}
                    </pre>
                  </div>
                  <div>
                    <h4 className="mb-2 font-medium">Extracted Filters</h4>
                    <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{JSON.stringify(turn.extractedFilters, null, 2) || "N/A"}</pre>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Card>

        <Card className="bg-muted p-4">
          <h3 className="mb-4 text-lg font-semibold">Flow Metrics</h3>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h4 className="mb-2 font-medium">Flow Coherence</h4>
              <div className={`text-2xl font-bold ${getScoreColor(data.flowCoherence)}`}>{(data.flowCoherence! * 100).toFixed(2)}%</div>
            </div>
            <div>
              <h4 className="mb-2 font-medium">Topic Transition Accuracy</h4>
              <div className={`text-2xl font-bold ${getScoreColor(data.topicTransitionAccuracy)}`}>{(data.topicTransitionAccuracy! * 100).toFixed(2)}%</div>
            </div>
          </div>
        </Card>

        <Card className="bg-muted p-4">
          <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
          <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
        </Card>
      </div>
    </>
  );
};

const RobustnessResultDetails: React.FC<{
  data: TransformedData;
  testCase: TestCase | undefined;
}> = ({ data, testCase }) => {
  const copyToClipboard = () => {
    const jsonData = JSON.stringify(
      {
        prompt: testCase?.prompt || "",
        expectedFilters: testCase?.expected_filters,
        extractedFilters: data.extractedFilters,
        filterAccuracy: data.filterAccuracy,
        noiseFiltering: data.noiseFiltering,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  return (
    <>
      <div className="flex justify-end">
        <CopyButton onClick={copyToClipboard} />
      </div>
      <Card className="bg-muted p-4">
        <h3 className="mb-4 text-lg font-semibold">Filter Analysis</h3>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-lg font-semibold">Expected Filters</h4>
            <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{JSON.stringify(testCase?.expected_filters, null, 2)}</pre>
          </div>
          <div>
            <h4 className="mb-2 text-lg font-semibold">Extracted Filters</h4>
            <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{JSON.stringify(data.extractedFilters, null, 2)}</pre>
          </div>
        </div>
      </Card>

      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Performance Metrics</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="mb-2 font-medium">Filter Accuracy</h4>
            <div className={`text-2xl font-bold ${getScoreColor(data.filterAccuracy)}`}>{(data.filterAccuracy! * 100).toFixed(2)}%</div>
          </div>
          <div>
            <h4 className="mb-2 font-medium">Noise Filtering</h4>
            <div className={`text-2xl font-bold ${getScoreColor(data.noiseFiltering)}`}>{(data.noiseFiltering! * 100).toFixed(2)}%</div>
          </div>
        </div>
      </Card>

      <Card className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Response</h3>
        <ChatMessageContent message={data.response} />
      </Card>

      {data.reasoning && (
        <Card className="bg-muted p-4">
          <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
          <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
        </Card>
      )}
    </>
  );
};

const DefensibilityResultDetails: React.FC<{
  data: TransformedData;
  testCase: TestCase | undefined;
}> = ({ data, testCase }) => {
  const copyToClipboard = () => {
    const jsonData = JSON.stringify(
      {
        prompt: testCase?.prompt || "",
        conversation: data.conversation,
        expectedResponses: testCase?.conversation?.map((turn) => turn.message),
        actualResponses: data.conversation?.map((turn) => turn.message.message),
        boundaryMaintenance: data.boundaryMaintenance,
      },
      null,
      2
    );
    navigator.clipboard.writeText(jsonData);
  };

  return (
    <>
      <div className="flex justify-end">
        <CopyButton onClick={copyToClipboard} />
      </div>

      <Card className="bg-muted p-4">
        <h3 className="mb-4 text-lg font-semibold">Boundary Maintenance Score</h3>
        <div className={`text-2xl font-bold ${getScoreColor(data.boundaryMaintenance)}`}>{(data.boundaryMaintenance! * 100).toFixed(2)}%</div>
      </Card>

      <Card className="bg-muted p-4">
        <h3 className="mb-4 text-lg font-semibold">Conversation Analysis</h3>
        {data.conversation?.map((turn, index) => (
          <div key={index} className="mb-6">
            <div className="mb-2 flex items-center gap-2">
              <Badge>Turn {index + 1}</Badge>
              <Badge variant="outline">{turn === data.conversation![0] ? "Initial Query" : "Follow-up"}</Badge>
            </div>
            <div className="space-y-4 rounded-lg bg-white p-4 shadow-sm">
              <div>
                <h4 className="mb-2 font-medium">Query</h4>
                <p className="text-gray-700">{testCase?.conversation?.[index]?.query || "N/A"}</p>
              </div>
              <Separator />
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="mb-2 font-medium">Expected Response</h4>
                  <div className="rounded bg-muted-foreground/10 p-2">
                    <p className="text-gray-700">{testCase?.conversation?.[index]?.message || "N/A"}</p>
                  </div>
                </div>
                <div>
                  <h4 className="mb-2 font-medium">Actual Response</h4>
                  <div className="rounded bg-muted-foreground/10 p-2">
                    <p className="text-gray-700">{turn.message.message}</p>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="mb-2 font-medium">Response Match</h4>
                <Badge variant={turn.message.message.trim() === testCase?.conversation?.[index]?.message?.trim() ? "success" : "destructive"}>
                  {turn.message.message.trim() === testCase?.conversation?.[index]?.message?.trim() ? "Matched" : "Mismatched"}
                </Badge>
              </div>
            </div>
          </div>
        ))}
      </Card>

      {data.reasoning && (
        <Card className="bg-muted p-4">
          <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
          <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
        </Card>
      )}
    </>
  );
};

export default ResultModal;
