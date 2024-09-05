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
  const calculateTokenCost = (tokenCount: number, model: Model) => {
    // TODO: this function should be updated to reflect the actual cost of the model,
    // input, and output cost for a model is not the same, for example for gpt-4o input token cost is 5$ per million tokens, while output token cost is 10$ per million tokens

    const costPerMillionTokens = model === "gpt-4o" ? 5 : 1;
    return (tokenCount / 1000000) * costPerMillionTokens;
  };

  const steps = ["classification", "expansion", "rerank", "generate"];

  const inputTotal = Object.values(metadata.inputTokenUsage).reduce((sum, value) => sum + value, 0);
  const outputTotal = Object.values(metadata.outputTokenUsage).reduce((sum, value) => sum + value, 0);
  const timeTotal = Object.values(metadata.timeTaken).reduce((sum, value) => sum + value, 0);

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
            <TableCell>{metadata.inputTokenUsage[step]?.toFixed(0) || "-"}</TableCell>
            <TableCell>{metadata.outputTokenUsage[step]?.toFixed(0) || "-"}</TableCell>
            <TableCell>{metadata.timeTaken[step]?.toFixed(2) || "-"}</TableCell>
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
          <TableCell>{calculateTokenCost(inputTotal, model).toFixed(4)}</TableCell>
          <TableCell>{calculateTokenCost(outputTotal, model).toFixed(4)}</TableCell>
          {/* TODO: We need to define a funtion that canlculates to total cost by adding the input and output costs  */}
          <TableCell>{calculateTokenCost(inputTotal, model).toFixed(4) + calculateTokenCost(outputTotal, model).toFixed(4)}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
});

export default ResponseMetadata;
