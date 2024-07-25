"use client";

import ChatComponent from "@/components/sections/ChatComponent";
import ProductComponent from "@/components/sections/ProductComponent";
import TestComponent from "@/components/sections/TestComponent";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AppContextActions, AppContextData, ChatState, useAppContext } from "@/context/appContext";
import { BotIcon, DownloadIcon, ImportIcon } from "lucide-react";
import Link from "next/link";
import React from "react";
import { Button } from "../ui/button";
import SettingsDropdown from "./SettingsDropdown";

const AppComponent: React.FC = () => {
  const { state, data, actions } = useAppContext();

  const handleTabChange = (value: string) => {
    switch (value) {
      case "chat":
        actions.select.chat();
        break;
      case "test":
        actions.select.test();
        break;
      case "products":
        actions.select.manageProducts();
        break;
    }
  };

  const handleImportState = (data: { importKey: string }) => {
    actions.submit.importState(data);
  };

  return (
    <Tabs defaultValue="test" className="w-full" onValueChange={handleTabChange}>
      <Header state={state.chatState} data={data} actions={actions} />
      <TabsContent value="chat">
        <ChatComponent />
      </TabsContent>
      <TabsContent value="test">
        <TestComponent />
      </TabsContent>
      <TabsContent value="products">
        <ProductComponent />
      </TabsContent>
    </Tabs>
  );
};

interface HeaderProps {
  state: ChatState;
  data: AppContextData;
  actions: AppContextActions;
}
const Header: React.FC<HeaderProps> = ({ state, data, actions }) => {
  return (
    <div className="flex w-full flex-row justify-between border-b bg-slate-100 px-6 py-3">
      <Logo />
      <Navigation />
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon">
          <DownloadIcon className="h-5 w-5 text-card-foreground" onClick={actions.click.exportState} />
          <ExportStateForm isOpen={state === "ExportingState"} onSubmit={actions.submit.exportState} onCancel={actions.cancel.exportState} />
        </Button>
        <Button variant="ghost" size="icon">
          <ImportIcon className="h-5 w-5 text-card-foreground" onClick={actions.click.importState} />
          <ImportStateForm isOpen={state === "ImportingState"} onSubmit={actions.submit.importState} onCancel={actions.cancel.importState} />
        </Button>
        <SettingsDropdown data={data} actions={actions} />
      </div>
    </div>
  );
};

const Logo: React.FC = () => (
  <Link href="#" className="flex items-center gap-2" prefetch={false}>
    <BotIcon className="h-6 w-6" />
    <span className="font-bold">BoardBot</span>
  </Link>
);

const Navigation: React.FC = () => (
  <TabsList className="grid w-[25%] grid-cols-3">
    <TabsTrigger value="chat">Chat</TabsTrigger>
    <TabsTrigger value="test">Test</TabsTrigger>
    <TabsTrigger value="products">Products</TabsTrigger>
  </TabsList>
);

/**
 * interface DeleteDocumentFormProps {
  onConfirm: () => void;
  onCancel: () => void;
}

const DeleteDocumentForm: React.FC<DeleteDocumentFormProps> = ({ onConfirm, onCancel }) => (
  <Dialog open={true} onOpenChange={onCancel}>
    <DialogContent>
      <DialogTitle>Delete Document</DialogTitle>
      <div className="py-4">
        <p>Are you sure you want to delete this document?</p>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onConfirm}>
          Confirm
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
 */

interface ImportStateFormProps {
  isOpen: boolean;
  onSubmit: (data: { importKey: string }) => void;
  onCancel: () => void;
}

const ImportStateForm: React.FC<ImportStateFormProps> = ({ isOpen, onSubmit, onCancel }) => {
  const [importKey, setImportKey] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ importKey });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      <DialogContent>
        <DialogTitle>Import State</DialogTitle>
        <div className="py-4">
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-2">
              <label htmlFor="importKey">Import Key</label>
              <input type="text" id="importKey" value={importKey} onChange={(e) => setImportKey(e.target.value)} className="input" />
            </div>
            <DialogFooter>
              <Button variant="outline" type="submit">
                Import
              </Button>
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </DialogFooter>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

interface ExportStateFormProps {
  isOpen: boolean;
  onSubmit: (data: { exportKey: string }) => void;
  onCancel: () => void;
}

const ExportStateForm: React.FC<ExportStateFormProps> = ({ isOpen, onSubmit, onCancel }) => {
  const [exportKey, setExportKey] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ exportKey });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      <DialogContent>
        <DialogTitle>Export State</DialogTitle>
        <div className="py-4">
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-2">
              <label htmlFor="exportKey">Export Key</label>
              <input type="text" id="exportKey" value={exportKey} onChange={(e) => setExportKey(e.target.value)} className="input" />
            </div>
            <DialogFooter>
              <Button variant="outline" type="submit">
                Export
              </Button>
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </DialogFooter>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AppComponent;
