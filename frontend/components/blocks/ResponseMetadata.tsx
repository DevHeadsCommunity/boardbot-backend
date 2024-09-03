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
    const costPerMillionTokens = model === "gpt-4o" ? 5 : 1; // Adjust this based on your pricing
    return (tokenCount / 1000000) * costPerMillionTokens;
  };

  const renderMetrics = (data: Record<string, number>, title: string, calculateTotal: boolean = true, isCost: boolean = false) => {
    const total = Object.values(data).reduce((sum, value) => sum + value, 0);
    return (
      <div className="mt-4">
        <h3 className="font-bold">{title}</h3>
        <ul>
          {Object.entries(data).map(([key, value]) => (
            <li key={key}>
              {key}: {value.toFixed(2)} {isCost ? "$" : ""}
            </li>
          ))}
          {calculateTotal && (
            <li className="font-bold">
              Total: {total.toFixed(2)} {isCost ? "$" : ""}
            </li>
          )}
        </ul>
        {title === "Input Token Usage" && <div>Cost: ${calculateTokenCost(total, model).toFixed(4)}</div>}
      </div>
    );
  };

  return (
    <div>
      {renderMetrics(metadata.inputTokenUsage, "Input Token Usage")}
      {renderMetrics(metadata.outputTokenUsage, "Output Token Usage")}
      {renderMetrics(metadata.timeTaken, "Time Taken (seconds)", true, false)}
    </div>
  );
});

export default ResponseMetadata;
