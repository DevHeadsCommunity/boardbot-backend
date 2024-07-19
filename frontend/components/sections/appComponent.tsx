"use client";

import ChatComponent from "@/components/sections/ChatComponent";
import ProductComponent from "@/components/sections/ProductComponent";
import TestComponent from "@/components/sections/TestComponent";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAppContext } from "@/context/appContext";

import React from "react";

interface AppComponentProps {}

const AppComponent: React.FC<AppComponentProps> = ({}) => {
  const { state, data, actions } = useAppContext();
  return (
    <Tabs defaultValue="test" className="w-full">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="chat" onClick={actions.select.chat} onSelect={actions.select.chat}>
          Chat
        </TabsTrigger>
        <TabsTrigger value="test" onClick={actions.select.test}>
          Test
        </TabsTrigger>
        <TabsTrigger value="products" onClick={actions.select.manageProducts}>
          Products
        </TabsTrigger>
      </TabsList>
      <TabsContent value="chat">
        <ChatComponent />
      </TabsContent>
      <TabsContent value="test">
        <TestComponent architecture={data.architecture} historyManagement={data.historyManagement} />
      </TabsContent>
      <TabsContent value="products">
        <ProductComponent />
      </TabsContent>
    </Tabs>
  );
};

export default AppComponent;
