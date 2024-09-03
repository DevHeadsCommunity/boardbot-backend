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
    <div className="grid grid-cols-2 gap-4">
      <div>
        <div>{message.message.response}</div>
        <ProductList products={message.message.products} />
        <div className="mt-2">
          <strong>Reasoning:</strong> {message.message.reasoning}
        </div>
        <div className="mt-2">
          <strong>Follow-up Question:</strong> {message.message.followUpQuestion}
        </div>
      </div>
      <div>
        <ResponseMetadata metadata={message.message.metadata} model={message.model} />
        <Button onClick={() => setIsModalOpen(true)} className="mt-4">
          More Details
        </Button>
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Full Response Data</DialogTitle>
            </DialogHeader>
            <pre className="max-h-[80vh] overflow-auto whitespace-pre-wrap">{JSON.stringify(message, null, 2)}</pre>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
});

export default BotResponse;
