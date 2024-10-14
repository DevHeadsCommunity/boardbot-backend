import { Button } from "@/components/ui/button";
import { ClipboardCopy } from "lucide-react";
import React from "react";

interface CopyButtonProps {
  onClick: () => void;
}

const CopyButton: React.FC<CopyButtonProps> = ({ onClick }) => (
  <Button onClick={onClick} variant="outline" size="sm" className="absolute right-2 top-2">
    <ClipboardCopy className="h-4 w-4" />
  </Button>
);

export default CopyButton;
