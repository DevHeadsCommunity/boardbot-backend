"use client";

import ChatComponent from "@/components/sections/ChatComponent";
import ProductComponent from "@/components/sections/ProductComponent";
import TestComponent from "@/components/sections/TestComponent";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AppContextActions, AppContextData, useAppContext } from "@/context/appContext";
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

  return (
    <Tabs defaultValue="test" className="w-full" onValueChange={handleTabChange}>
      <Header data={data} actions={actions} />
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
  data: AppContextData;
  actions: AppContextActions;
}
const Header: React.FC<HeaderProps> = ({ data, actions }) => (
  <div className="flex w-full flex-row justify-between border-b bg-slate-100 px-6 py-3">
    <Logo />
    <Navigation />
    <div className="flex items-center gap-4">
      <Button variant="ghost" size="icon">
        <DownloadIcon className="h-5 w-5 text-card-foreground" />
      </Button>
      <Button variant="ghost" size="icon">
        <ImportIcon className="h-5 w-5 text-card-foreground" />
      </Button>
      <SettingsDropdown data={data} actions={actions} />
    </div>
  </div>
);

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
