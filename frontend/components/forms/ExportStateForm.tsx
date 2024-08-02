import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { useState } from "react";

interface StateFormProps {
  isOpen: boolean;
  onCancel: () => void;
}

interface ExportStateFormProps extends StateFormProps {
  onSubmit: (fileName: string) => void;
}

const ExportStateForm: React.FC<ExportStateFormProps> = ({ isOpen, onSubmit, onCancel }) => {
  const [fileName, setFileName] = useState("boardbot_state.json");
  const [filePath, setFilePath] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let directoryPath = "";

    try {
      const directoryHandle = await (window as any).showDirectoryPicker({
        startIn: "downloads",
      });

      // Getting the directory path
      directoryPath = directoryHandle.name;

      if (directoryHandle) {
        setFilePath(directoryHandle.name);
      }
    } catch (err) {
      console.log("Directory selection failed or not supported, defaulting to Downloads");
      directoryPath = "downloads";
    }

    // Construct the full file path
    const fullPath = `${directoryPath}/${fileName}`;
    onSubmit(fullPath);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogTitle>Export State</DialogTitle>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fileName">File Name</Label>
            <Input id="fileName" value={fileName} onChange={(e) => setFileName(e.target.value)} placeholder="boardbot_state.json" />
          </div>
          <DialogFooter>
            <Button type="submit">Export</Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ExportStateForm;
