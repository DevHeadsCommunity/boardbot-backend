"use client";

import { DatabaseZap } from "lucide-react";

const ProductComponent = () => {
  return (
    <div className="flex min-h-screen flex-col items-center bg-background">
      <header className="flex w-full items-start border-b bg-card px-4 py-3 sm:px-6">
        <div className="flex items-start gap-4">
          <DatabaseZap className="h-6 w-6 text-card-foreground" />
          <h1 className="text-lg font-semibold text-card-foreground">Product Vector Store Manager</h1>
        </div>
      </header>
      <div className="flex h-screen w-full flex-col items-center justify-center">
        <h1 className="mb-5 text-2xl font-bold">Manage Vector Store</h1>
      </div>
    </div>
  );
};

export default ProductComponent;
