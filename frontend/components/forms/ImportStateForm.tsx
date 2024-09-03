import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { memo, useRef, useState } from "react";
import { toast } from "react-toastify";

interface ImportStateFormProps {
  isOpen: boolean;
  onSubmit: (data: { file: File }) => void;
  onCancel: () => void;
}

const ImportStateForm: React.FC<ImportStateFormProps> = memo(function ImportStateForm({ isOpen, onSubmit, onCancel }) {
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error("Please select a file to import.");
      return;
    }
    onSubmit({ file });
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== "application/json") {
        toast.error("Please select a valid JSON file.");
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogTitle>Import State</DialogTitle>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Select File</Label>
            <div className="flex items-center space-x-2">
              <Input value={file ? file.name : ""} placeholder="No file selected" readOnly />
              <Button type="button" onClick={handleFileSelect}>
                Browse
              </Button>
            </div>
            <input type="file" ref={fileInputRef} accept=".json" style={{ display: "none" }} onChange={handleFileChange} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!file}>
              Import
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
});

export default ImportStateForm;
