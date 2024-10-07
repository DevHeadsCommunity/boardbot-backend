import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { AddProductState, ProductActions } from "@/hooks/useProductContext";
import { AddProductSchema, Product } from "@/types/productTypes";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { z } from "zod";

interface AddProductProps {
  state: AddProductState;
  actions: ProductActions;
}

const initialProductState: z.infer<typeof AddProductSchema> = {
  productId: "",
  name: "",
  manufacturer: "",
  formFactor: "",
  evaluationOrCommercialization: "",
  processorArchitecture: "",
  processorCoreCount: "",
  processorManufacturer: "",
  processorTdp: "",
  memory: "",
  onboardStorage: "",
  inputVoltage: "",
  ioCount: [],
  wireless: [],
  operatingSystemBsp: [],
  operatingTemperatureMax: "",
  operatingTemperatureMin: "",
  certifications: [],
  price: "",
  stockAvailability: "",
};

const formatLabel = (key: string): string => {
  return key
    .split(/(?=[A-Z])/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const AddProduct = ({ state, actions }: AddProductProps) => {
  const [newProduct, setNewProduct] = useState<z.infer<typeof AddProductSchema>>(initialProductState);
  const [rawData, setRawData] = useState("");
  const [rawDataProductId, setRawDataProductId] = useState("");
  const [maxMissingFeatureAttempts, setMaxMissingFeatureAttempts] = useState(3);
  const [maxLowConfidenceAttempts, setMaxLowConfidenceAttempts] = useState(3);
  const [maxNoProgressAttempts, setMaxNoProgressAttempts] = useState(3);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [batchSize, setBatchSize] = useState(5);

  const [file, setFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState("newProduct");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewProduct((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleAddProduct = () => {
    switch (activeTab) {
      case "newProduct":
        actions.submit.addProduct(newProduct as Product);
        break;
      case "rawData":
        actions.submit.addProductRawData(rawDataProductId, rawData, maxMissingFeatureAttempts, maxLowConfidenceAttempts, maxNoProgressAttempts, confidenceThreshold);
        break;
      case "file":
        if (file) {
          actions.submit.addProductsRawData(file, maxMissingFeatureAttempts, maxLowConfidenceAttempts, maxNoProgressAttempts, confidenceThreshold, batchSize);
        }
        break;
    }
  };

  const renderNewProductForm = () => (
    <ScrollArea className="h-[60vh] pr-4">
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(newProduct).map(([key, value]) => {
          const isTextArea = key === "fullProductDescription" || key === "fullSummary" || key === "shortSummary";
          const isArray = Array.isArray(value);
          return (
            <div key={key} className={isTextArea ? "col-span-2" : ""}>
              <Label htmlFor={key}>{formatLabel(key)}</Label>
              {isTextArea ? (
                <Textarea id={key} name={key} value={value as string} onChange={handleInputChange} />
              ) : isArray ? (
                <Input id={key} name={key} value={(value as string[]).join(", ")} onChange={(e) => setNewProduct((prev) => ({ ...prev, [key]: e.target.value.split(", ") }))} />
              ) : (
                <Input id={key} name={key} value={value as string} onChange={handleInputChange} />
              )}
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );

  const renderRawDataForm = () => (
    <div className="space-y-4">
      <div>
        <Label htmlFor="rawDataProductId">Product ID</Label>
        <Input id="rawDataProductId" value={rawDataProductId} onChange={(e) => setRawDataProductId(e.target.value)} required />
      </div>
      <div>
        <Label htmlFor="rawData">Raw Data</Label>
        <Textarea id="rawData" value={rawData} onChange={(e) => setRawData(e.target.value)} required />
      </div>
      <div>
        <Label htmlFor="maxMissingFeatureAttempts">Max Missing Feature Attempts</Label>
        <Input id="maxMissingFeatureAttempts" type="number" value={maxMissingFeatureAttempts} onChange={(e) => setMaxMissingFeatureAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="maxLowConfidenceAttempts">Max Low Confidence Attempts</Label>
        <Input id="maxLowConfidenceAttempts" type="number" value={maxLowConfidenceAttempts} onChange={(e) => setMaxLowConfidenceAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="maxNoProgressAttempts">Max No Progress Attempts</Label>
        <Input id="maxNoProgressAttempts" type="number" value={maxNoProgressAttempts} onChange={(e) => setMaxNoProgressAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="confidenceThreshold">Confidence Threshold</Label>
        <Input id="confidenceThreshold" type="number" step="0.1" value={confidenceThreshold} onChange={(e) => setConfidenceThreshold(Number(e.target.value))} required />
      </div>
    </div>
  );

  const renderFileUploadForm = () => (
    <div className="space-y-4">
      <Label htmlFor="file">CSV File</Label>
      <Input id="file" type="file" onChange={handleFileChange} required />
      <div>
        <Label htmlFor="batchSize">Batch Size</Label>
        <Input id="batchSize" type="number" value={batchSize} onChange={(e) => setBatchSize(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="maxMissingFeatureAttempts">Max Missing Feature Attempts</Label>
        <Input id="maxMissingFeatureAttempts" type="number" value={maxMissingFeatureAttempts} onChange={(e) => setMaxMissingFeatureAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="maxLowConfidenceAttempts">Max Low Confidence Attempts</Label>
        <Input id="maxLowConfidenceAttempts" type="number" value={maxLowConfidenceAttempts} onChange={(e) => setMaxLowConfidenceAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="maxNoProgressAttempts">Max No Progress Attempts</Label>
        <Input id="maxNoProgressAttempts" type="number" value={maxNoProgressAttempts} onChange={(e) => setMaxNoProgressAttempts(Number(e.target.value))} required />
      </div>
      <div>
        <Label htmlFor="confidenceThreshold">Confidence Threshold</Label>
        <Input id="confidenceThreshold" type="number" step="0.1" value={confidenceThreshold} onChange={(e) => setConfidenceThreshold(Number(e.target.value))} required />
      </div>
    </div>
  );

  const render = () => {
    if (state === AddProductState.AddingProduct || state === AddProductState.AddingProductFormRawData || state === AddProductState.AddingProductsFormRawData) {
      return (
        <div className="flex h-full items-center justify-center">
          <Loader2 className="mr-2 h-16 w-16 animate-spin" />
        </div>
      );
    }

    return (
      <Dialog open={state === AddProductState.DisplayingForm} onOpenChange={() => actions.cancel.addProduct()}>
        <DialogContent className="sm:max-w-[800px]">
          <DialogHeader>
            <DialogTitle>Add Product</DialogTitle>
          </DialogHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="newProduct">New Product</TabsTrigger>
              <TabsTrigger value="rawData">Raw Data</TabsTrigger>
              <TabsTrigger value="file">File Upload</TabsTrigger>
            </TabsList>
            <TabsContent value="newProduct">{renderNewProductForm()}</TabsContent>
            <TabsContent value="rawData">{renderRawDataForm()}</TabsContent>
            <TabsContent value="file">{renderFileUploadForm()}</TabsContent>
          </Tabs>
          <DialogFooter>
            <Button variant="outline" onClick={actions.cancel.addProduct}>
              Close
            </Button>
            <Button onClick={handleAddProduct}>Add Product</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  };

  return render();
};

export default AddProduct;
