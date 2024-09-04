import { ResponseMessage } from "@/types";
import React, { memo, useState } from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import ProductList from "./ProductList";
import ResponseMetadata from "./ResponseMetadata";

interface BotResponseProps {
  message: ResponseMessage;
}

const BotResponse: React.FC<BotResponseProps> = memo(function BotResponse({ message }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="flex">
      <div className="flex-grow pr-4">
        <p className="mb-2">{message.message.response}</p>
        <ProductList products={message.message.products} />
        <div className="mt-2">
          <strong>Reasoning:</strong> {message.message.reasoning}
        </div>
        <div className="mt-2 text-blue-600">
          <strong>Follow-up:</strong> {message.message.followUpQuestion}
        </div>
      </div>
      <div className="w-2/5 rounded-lg bg-gray-200 p-3 text-sm">
        <ResponseMetadata metadata={message.message.metadata} model={message.model} />
        <Button onClick={() => setIsModalOpen(true)} variant="outline" size="sm" className="mt-2 w-full">
          More Details
        </Button>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Full Response Data</DialogTitle>
            </DialogHeader>
            <pre className="max-h-[300px] overflow-auto rounded-md bg-gray-100 p-4">{JSON.stringify(message, null, 2)}</pre>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
});

export default BotResponse;
