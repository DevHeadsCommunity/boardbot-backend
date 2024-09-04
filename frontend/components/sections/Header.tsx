import { TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AppContextActions, AppContextData, AppState } from "@/hooks/useAppContext";
import { BotIcon, DownloadIcon, ImportIcon } from "lucide-react";
import Link from "next/link";
import React, { memo } from "react";
import ExportStateForm from "../forms/ExportStateForm";
import ImportStateForm from "../forms/ImportStateForm";
import { Button } from "../ui/button";
import SettingsDropdown from "./SettingsDropdown";

interface HeaderProps {
  state: AppState;
  data: AppContextData;
  actions: AppContextActions;
}

const Header: React.FC<HeaderProps> = memo(function Header({ state, data, actions }) {
  return (
    <div className="flex w-full flex-row justify-between border-b bg-slate-100 px-20 py-3">
      <Logo />
      <Navigation />
      <div className="flex items-center gap-4">
        <ExportButton state={state} actions={actions} />
        <ImportButton state={state} actions={actions} />
        <SettingsDropdown data={data} actions={actions} />
      </div>
    </div>
  );
});

const Logo: React.FC = memo(function Logo() {
  return (
    <Link href="#" className="flex items-center gap-2" prefetch={false}>
      <BotIcon className="h-6 w-6" />
      <span className="font-bold">BoardBot</span>
    </Link>
  );
});

const Navigation: React.FC = memo(function Navigation() {
  return (
    <TabsList className="grid w-[25%] grid-cols-3">
      <TabsTrigger value="chat">Chat</TabsTrigger>
      <TabsTrigger value="test">Test</TabsTrigger>
      <TabsTrigger value="products">Products</TabsTrigger>
    </TabsList>
  );
});

const ExportButton: React.FC<{ state: AppState; actions: AppContextActions }> = memo(function ExportButton({ state, actions }) {
  return (
    <>
      <Button variant="ghost" size="icon" onClick={actions.select.exportState}>
        <DownloadIcon className="h-5 w-5 text-card-foreground" />
      </Button>
      <ExportStateForm isOpen={state === AppState.Exporting} onSubmit={(data) => actions.submit.exportState(data.fileName)} onCancel={actions.cancel.exportState} />
    </>
  );
});

const ImportButton: React.FC<{ state: AppState; actions: AppContextActions }> = memo(function ImportButton({ state, actions }) {
  return (
    <>
      <Button variant="ghost" size="icon" onClick={actions.select.importState}>
        <ImportIcon className="h-5 w-5 text-card-foreground" />
      </Button>
      <ImportStateForm isOpen={state === AppState.Importing} onSubmit={(data) => actions.submit.importState(data.file)} onCancel={actions.cancel.importState} />
    </>
  );
});

export default Header;
