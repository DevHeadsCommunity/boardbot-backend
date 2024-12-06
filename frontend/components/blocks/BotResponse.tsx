import { DisplayProductState, useProductContext } from "@/hooks/useProductContext";
import { Product, ResponseMessage } from "@/types";
import React, { memo, useState } from "react";
import ProductDetail from "../sections/ProductDetail";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import ChatMessageContent from "./ChatMessageContent";
import ProductList from "./ProductList";
import ResponseMetadata from "./ResponseMetadata";

interface BotResponseProps {
  message: ResponseMessage;
}

const BotResponse: React.FC<BotResponseProps> = memo(function BotResponse({ message }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const { actions, data } = useProductContext();
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  return (
    <div className="flex">
      <div className="flex-grow pr-4">
        <p className="mb-2">{message.message.message}</p>
        <ProductList
          products={message.message.products || []}
          onProductSelect={(product) => {
            setSelectedProduct(product);
            setIsProductModalOpen(true);
          }}
        />
        <div className="mt-2">
          <strong>Reasoning:</strong> {message.message.reasoning}
        </div>
        <div className="mt-2 text-blue-600">
          <strong>Follow-up:</strong>{" "}
          {Array.isArray(message.message.followUpQuestion) ? (
            <ul className="list-disc pl-5">
              {message.message.followUpQuestion.map((question, index) => (
                <li key={index}>{question}</li>
              ))}
            </ul>
          ) : (
            message.message.followUpQuestion
          )}
        </div>
      </div>
      <div className="w-2/5 rounded-lg bg-gray-200 p-3 text-sm">
        <ResponseMetadata
          metadata={
            message.message.metadata || {
              inputTokenUsage: {},
              outputTokenUsage: {},
              timeTaken: {},
            }
          }
          model={message.model}
        />
        <Button onClick={() => setIsModalOpen(true)} variant="outline" size="sm" className="mt-2 w-full">
          More Details
        </Button>

        {/* Message Details Modal */}
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent className="max-h-[80vh] max-w-7xl overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Test Result: {message.messageId}</DialogTitle>
            </DialogHeader>
            <ChatMessageContent message={JSON.stringify(message, null, 2)} />
          </DialogContent>
        </Dialog>

        {/* Product Details Modal */}
        {isProductModalOpen && (
          <ProductDetail
            state={DisplayProductState.DisplayingProduct}
            product={selectedProduct}
            actions={{
              ...actions,
              close: {
                ...actions.close,
                productDetailModal: () => setIsProductModalOpen(false),
              },
            }}
            displayOnly={true}
          />
        )}
      </div>
    </div>
  );
});

export default BotResponse;
