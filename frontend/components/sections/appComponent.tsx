"use client";

import ChatComponent from "@/components/sections/ChatComponent";
import ProductComponent from "@/components/sections/ProductComponent";
import TestComponent from "@/components/sections/TestComponent";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { AppState, useAppContext } from "@/hooks/useAppContext";
import React, { useCallback } from "react";
import Header from "./Header";

const AppComponent: React.FC = () => {
  const { state, data, actions } = useAppContext();

  const handleTabChange = useCallback(
    (value: string) => {
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
    },
    [actions]
  );

  console.log("Rendering AppComponent", state.appState);

  return (
    <Tabs defaultValue="chat" className="w-full " onValueChange={handleTabChange}>
      <Header state={state.appState} data={data} actions={actions} />
      <TabsContent value="chat">{state.appState === AppState.Chatting && <ChatComponent />}</TabsContent>
      <TabsContent value="test">{state.appState === AppState.Testing && <TestComponent />}</TabsContent>
      <TabsContent value="products">{state.appState === AppState.Managing && <ProductComponent />}</TabsContent>
    </Tabs>
  );
};

export default React.memo(AppComponent);
