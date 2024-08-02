"use client";

import ChatComponent from "@/components/sections/ChatComponent";
import ProductComponent from "@/components/sections/ProductComponent";
import TestComponent from "@/components/sections/TestComponent";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AppContextActions, AppContextData, AppState, useAppContext } from "@/hooks/useAppContext";
import { BotIcon, DownloadIcon, ImportIcon } from "lucide-react";
import Link from "next/link";
import React from "react";
import ExportStateForm from "../forms/ExportStateForm";
import ImportStateForm from "../forms/ImportStateForm";
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

  return (
    <Tabs defaultValue="chat" className="w-full" onValueChange={handleTabChange}>
      <Header state={state.appState} data={data} actions={actions} />
      <TabsContent value="chat">{state.appState === AppState.Chatting && <ChatComponent />}</TabsContent>
      <TabsContent value="test">{state.appState === AppState.Testing && <TestComponent />}</TabsContent>
      <TabsContent value="products">{state.appState === AppState.ManagingProducts && <ProductComponent />}</TabsContent>
    </Tabs>
  );
};

interface HeaderProps {
  state: AppState;
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
          <ExportStateForm isOpen={state === AppState.DisplayingExportStateForm} onSubmit={actions.submit.exportState} onCancel={actions.cancel.exportState} />
        </Button>
        <Button variant="ghost" size="icon">
          <ImportIcon className="h-5 w-5 text-card-foreground" onClick={actions.click.importState} />
          <ImportStateForm isOpen={state === AppState.DisplayingImportStateForm} onSubmit={actions.submit.importState} onCancel={actions.cancel.importState} />
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

export default AppComponent;
