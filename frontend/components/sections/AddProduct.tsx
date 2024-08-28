import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AddProductState, ProductActions } from "@/hooks/useProductContext";
import { Product } from "@/types";
import { Loader2 } from "lucide-react";
import { useState } from "react";

interface AddProductProps {
  state: AddProductState;
  actions: ProductActions;
}

const initialProductState: Product = {
  name: "",
  manufacturer: "",
  formFactor: "",
  processor: "",
  coreCount: 0,
  processorTdp: 0,
  memory: 0,
  io: "",
  operatingSystem: "",
  environmentals: "",
  certifications: "",
  shortSummary: "",
  fullSummary: "",
  fullProductDescription: "",
  ids: "",
};

const AddProduct = ({ state, actions }: AddProductProps) => {
  const [newProduct, setNewProduct] = useState<Product>(initialProductState);
  const [rawData, setRawData] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setNewProduct((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddProduct = (e: React.FormEvent) => {
    e.preventDefault();
    actions.submit.addProduct(newProduct);
  };

  const handleAddRawProduct = (e: React.FormEvent) => {
    e.preventDefault();
    actions.submit.addProductRawData(newProduct.ids, rawData);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleAddProductsFromFile = (e: React.FormEvent) => {
    e.preventDefault();
    if (file) {
      actions.submit.addProductsRawData(file);
    }
  };

  const render = () => {
    switch (state) {
      case AddProductState.Idle:
        return null;
      case AddProductState.DisplayingForm:
        return (
          <Card className="mx-auto w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Add New Product</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddProduct} className="space-y-4">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" name="name" value={newProduct.name} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="manufacturer">Manufacturer</Label>
                  <Input id="manufacturer" name="manufacturer" value={newProduct.manufacturer} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="formFactor">Form Factor</Label>
                  <Input id="formFactor" name="formFactor" value={newProduct.formFactor} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="processor">Processor</Label>
                  <Input id="processor" name="processor" value={newProduct.processor} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="coreCount">Core Count</Label>
                  <Input id="coreCount" name="coreCount" type="number" value={newProduct.coreCount} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="memory">Memory</Label>
                  <Input id="memory" name="memory" type="number" value={newProduct.memory} onChange={handleInputChange} required />
                </div>
                <div>
                  <Label htmlFor="operatingSystem">Operating System</Label>
                  <Input id="operatingSystem" name="operatingSystem" value={newProduct.operatingSystem} onChange={handleInputChange} required />
                </div>
                <div className="flex justify-end space-x-4">
                  <Button type="submit">Add Product</Button>
                  <Button variant="outline" onClick={actions.cancel.addProduct}>
                    Cancel
                  </Button>
                </div>
              </form>

              <div className="mt-8">
                <h3 className="mb-4 text-lg font-semibold">Add Product from Raw Data</h3>
                <form onSubmit={handleAddRawProduct} className="space-y-4">
                  <div>
                    <Label htmlFor="rawData">Raw Data</Label>
                    <Input id="rawData" name="rawData" value={rawData} onChange={(e) => setRawData(e.target.value)} required />
                  </div>
                  <div className="flex justify-end">
                    <Button type="submit">Add Raw Product</Button>
                  </div>
                </form>
              </div>

              <div className="mt-8">
                <h3 className="mb-4 text-lg font-semibold">Add Products from File</h3>
                <form onSubmit={handleAddProductsFromFile} className="space-y-4">
                  <div>
                    <Label htmlFor="file">CSV File</Label>
                    <Input id="file" name="file" type="file" onChange={handleFileChange} required />
                  </div>
                  <div className="flex justify-end">
                    <Button type="submit">Add Products from File</Button>
                  </div>
                </form>
              </div>
            </CardContent>
          </Card>
        );
      case AddProductState.AddingProduct:
      case AddProductState.AddingProductFormRawData:
      case AddProductState.AddingProductsFormRawData:
        return (
          <div className="flex h-screen items-center justify-center">
            <Loader2 className="mr-2 h-16 w-16 animate-spin" />
          </div>
        );
      default:
        return null;
    }
  };

  return render();
};

export default AddProduct;
