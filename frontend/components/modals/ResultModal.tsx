import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import React from "react";
import ChatMessageContent from "../blocks/ChatMessageContent";
import { TransformedData } from "../cards/TestResultCard";

interface ResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: TransformedData;
}

const ResultModal: React.FC<ResultModalProps> = ({ isOpen, onClose, data }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Test Result: {data.messageId}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[80vh] overflow-y-auto">
          <div className="space-y-6 p-4">
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
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Metrics</h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                {data.testType === "accuracy" && (
                  <>
                    <MetricItem label="Product Accuracy" value={`${(data.productAccuracy! * 100).toFixed(2)}%`} />
                    <MetricItem label="Feature Accuracy" value={`${(data.featureAccuracy! * 100).toFixed(2)}%`} />
                  </>
                )}
                {data.testType === "consistency" && (
                  <>
                    <MetricItem label="Product Consistency" value={`${(data.productConsistency! * 100).toFixed(2)}%`} />
                    <MetricItem label="Order Consistency" value={`${(data.orderConsistency! * 100).toFixed(2)}%`} />
                  </>
                )}
              </div>
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Input</h3>
              <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.input}</pre>
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Response</h3>
              <ChatMessageContent message={data.response} />
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Products</h3>
              <ChatMessageContent message={JSON.stringify(data.products, null, 2)} />
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Reasoning</h3>
              <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.reasoning}</pre>
            </Card>
            <Card className="bg-muted p-4">
              <h3 className="mb-2 text-lg font-semibold">Follow-up Question</h3>
              <pre className="whitespace-pre-wrap break-words rounded bg-muted-foreground/10 p-2">{data.followUpQuestion}</pre>
            </Card>
            {data.tags && data.tags.length > 0 && (
              <Card className="bg-muted p-4">
                <h3 className="mb-2 text-lg font-semibold">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {data.tags.map((tag, index) => (
                    <span key={index} className="rounded bg-primary/10 px-2 py-1 text-sm">
                      {tag}
                    </span>
                  ))}
                </div>
              </Card>
            )}
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

const MetricItem: React.FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div>
    <p className="text-sm font-medium text-muted-foreground">{label}</p>
    <p className="text-lg font-semibold">{value}</p>
  </div>
);

export default ResultModal;
