import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { TestCase } from "@/types";
import React from "react";
import ChatMessageContent from "../blocks/ChatMessageContent";
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

const ConsistencyResultDetails: React.FC<{ data: TransformedData; testCase: TestCase | undefined }> = ({ data, testCase }) => (
  <>
    <Card className="bg-muted p-4">
      <h3 className="mb-2 text-lg font-semibold">Main Prompt Response</h3>
      <ChatMessageContent message={data.response} />
      <h4 className="text-md mt-4 font-semibold">Products</h4>
      <ChatMessageContent message={JSON.stringify(data.products, null, 2)} />
      <h4 className="text-md mt-4 font-semibold">Reasoning</h4>
      <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
    </Card>
    {data.variationResponses?.map((variation, index) => (
      <Card key={index} className="bg-muted p-4">
        <h3 className="mb-2 text-lg font-semibold">Variation {index + 1}</h3>
        <h4 className="text-md mb-2 font-semibold">Prompt</h4>
        <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{testCase?.variations?.[index]}</pre>
        <h4 className="text-md mt-4 font-semibold">Response</h4>
        <ChatMessageContent message={variation.response} />
        <h4 className="text-md mt-4 font-semibold">Products</h4>
        <ChatMessageContent message={JSON.stringify(variation.products, null, 2)} />
        <h4 className="text-md mt-4 font-semibold">Reasoning</h4>
        <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{variation.reasoning}</pre>
      </Card>
    ))}
  </>
);

const MetricItem: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div>
    <p className="text-sm font-medium text-muted-foreground">{label}</p>
    <p className="text-lg font-semibold">{value}</p>
  </div>
);

export default ResultModal;
