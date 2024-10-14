import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
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
          <DialogTitle>Test Result: {data.messageId}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[80vh] overflow-y-auto">
          <div className="space-y-6 p-4">
            <GeneralInformation data={data} />
            <Metrics data={data} />
            <TestInput testCase={testCase} />
            {data.testType === "accuracy" ? <AccuracyResultDetails data={data} testCase={testCase} /> : <ConsistencyResultDetails data={data} testCase={testCase} />}
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
      {data.testType === "accuracy" ? (
        <>
          <MetricItem label="Product Accuracy" value={`${(data.productAccuracy! * 100).toFixed(2)}%`} />
          <MetricItem label="Feature Accuracy" value={`${(data.featureAccuracy! * 100).toFixed(2)}%`} />
        </>
      ) : (
        <>
          <MetricItem label="Product Consistency" value={`${(data.productConsistency! * 100).toFixed(2)}%`} />
          <MetricItem label="Order Consistency" value={`${(data.orderConsistency! * 100).toFixed(2)}%`} />
        </>
      )}
    </div>
  </Card>
);

const TestInput: React.FC<{ testCase: TestCase | undefined }> = ({ testCase }) => (
  <Card className="bg-muted p-4">
    <h3 className="mb-2 text-lg font-semibold">Test Input</h3>
    <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{testCase?.prompt}</pre>
  </Card>
);

const AccuracyResultDetails: React.FC<{ data: TransformedData; testCase: TestCase | undefined }> = ({ data, testCase }) => (
  <>
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

const MetricItem: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div>
    <p className="text-sm font-medium text-muted-foreground">{label}</p>
    <p className="text-lg font-semibold">{value}</p>
  </div>
);

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

export default ResultModal;
