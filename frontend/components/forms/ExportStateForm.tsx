import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { memo, useState } from "react";
import { toast } from "react-toastify";

interface ExportStateFormProps {
  isOpen: boolean;
  onSubmit: (data: { fileName: string }) => void;
  onCancel: () => void;
}

const ExportStateForm: React.FC<ExportStateFormProps> = memo(function ExportStateForm({ isOpen, onSubmit, onCancel }) {
  const [fileName, setFileName] = useState("boardbot_state.json");
  const [directoryPath, setDirectoryPath] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let selectedDirectoryPath = "";

    try {
      const directoryHandle = await (window as any).showDirectoryPicker({
        startIn: "downloads",
      });

      selectedDirectoryPath = await directoryHandle.name;
      setDirectoryPath(selectedDirectoryPath);
    } catch (err) {
      console.log("Directory selection failed or not supported, defaulting to Downloads");
      selectedDirectoryPath = "Downloads";
    }

    const fullPath = `${selectedDirectoryPath}/${fileName}`;
    console.log("====> Exporting state to", fullPath);
    onSubmit({ fileName: fullPath });
    toast.success(`State exported to ${fullPath}`);
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
          {directoryPath && (
            <div className="space-y-2">
              <Label>Selected Directory</Label>
              <Input value={directoryPath} readOnly />
            </div>
          )}
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
});

export default ExportStateForm;
