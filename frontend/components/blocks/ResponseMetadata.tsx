import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Model } from "@/types";
import React, { memo } from "react";

interface ResponseMetadataProps {
  metadata: {
    inputTokenUsage: Record<string, number>;
    outputTokenUsage: Record<string, number>;
    timeTaken: Record<string, number>;
  };
  model: Model;
}

const ResponseMetadata: React.FC<ResponseMetadataProps> = memo(function ResponseMetadata({ metadata, model }) {
  const calculateTokenCost = (tokenCount: number, model: Model, isOutput: boolean) => {
    let costPerMillionTokens;
    if (model === "gpt-4o") {
      costPerMillionTokens = isOutput ? 10 : 2.5; // $10 per million output tokens, $2.5 per million input tokens
    } else {
      costPerMillionTokens = isOutput ? 2 : 1; // Example rates for other models, adjust as needed
    }
    return (tokenCount / 1000000) * costPerMillionTokens;
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(2)}`;
  };

  const steps = Object.keys(metadata?.timeTaken || {});
  const inputTotal = Object.values(metadata?.inputTokenUsage || {}).reduce((sum, value) => sum + value, 0);
  const outputTotal = Object.values(metadata?.outputTokenUsage || {}).reduce((sum, value) => sum + value, 0);
  const timeTotal = Object.values(metadata?.timeTaken || {}).reduce((sum, value) => sum + value, 0);

  const inputCost = calculateTokenCost(inputTotal, model, false);
  const outputCost = calculateTokenCost(outputTotal, model, true);
  const totalCost = inputCost + outputCost;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Step</TableHead>
          <TableHead>Input</TableHead>
          <TableHead>Output</TableHead>
          <TableHead>Time</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {steps.map((step) => (
          <TableRow key={step}>
            <TableCell className="font-bold">{step}</TableCell>
            <TableCell>{metadata?.inputTokenUsage[step]?.toFixed(0) || "-"}</TableCell>
            <TableCell>{metadata?.outputTokenUsage[step]?.toFixed(0) || "-"}</TableCell>
            <TableCell>{metadata?.timeTaken[step]?.toFixed(2) || "-"}</TableCell>
          </TableRow>
        ))}
        <TableRow>
          <TableCell className="font-bold">Total</TableCell>
          <TableCell>{inputTotal.toFixed(0)}</TableCell>
          <TableCell>{outputTotal.toFixed(0)}</TableCell>
          <TableCell>{timeTotal.toFixed(2)}</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-bold">Cost</TableCell>
          <TableCell>{formatCost(inputCost)}</TableCell>
          <TableCell>{formatCost(outputCost)}</TableCell>
          <TableCell>{formatCost(totalCost)}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
});

export default ResponseMetadata;
