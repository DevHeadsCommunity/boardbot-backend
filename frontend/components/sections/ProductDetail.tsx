import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DisplayProductState, ProductActions } from "@/hooks/useProductContext";
import { Product } from "@/types";
import { Loader2 } from "lucide-react";
import { useState } from "react";

interface ProductDetailProps {
  state: DisplayProductState;
  product: Product;
  actions: ProductActions;
}

const ProductDetail = ({ state, product, actions }: ProductDetailProps) => {
  const [editedProduct, setEditedProduct] = useState<Product>(product);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEditedProduct((prev) => ({ ...prev, [name]: value }));
  };

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    actions.submit.updateProduct(editedProduct);
  };

  const handleDeleteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    actions.submit.deleteProduct(product.name);
  };

  const render = () => {
    switch (state) {
      case DisplayProductState.Idle:
        return null;
      case DisplayProductState.DisplayingProduct:
        return (
          <Card className="mx-auto w-full max-w-2xl">
            <CardHeader>
              <CardTitle>{product.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Manufacturer</Label>
                  <p>{product.manufacturer}</p>
                </div>
                <div>
                  <Label>Form Factor</Label>
                  <p>{product.formFactor}</p>
                </div>
                <div>
                  <Label>Processor</Label>
                  <p>{product.processor}</p>
                </div>
                <div>
                  <Label>Core Count</Label>
                  <p>{product.coreCount}</p>
                </div>
                <div>
                  <Label>Memory</Label>
                  <p>{product.memory}</p>
                </div>
                <div>
                  <Label>Operating System</Label>
                  <p>{product.operatingSystem}</p>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-4">
                <Button onClick={actions.click.selectUpdateProduct}>Update Product</Button>
                <Button variant="destructive" onClick={actions.click.selectDeleteProduct}>
                  Delete Product
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      case DisplayProductState.DisplayingUpdateProductForm:
        return (
          <Card className="mx-auto w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Update Product: {product.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="manufacturer">Manufacturer</Label>
                  <Input id="manufacturer" name="manufacturer" value={editedProduct.manufacturer} onChange={handleInputChange} />
                </div>
                <div>
                  <Label htmlFor="formFactor">Form Factor</Label>
                  <Input id="formFactor" name="formFactor" value={editedProduct.formFactor} onChange={handleInputChange} />
                </div>
                <div>
                  <Label htmlFor="processor">Processor</Label>
                  <Input id="processor" name="processor" value={editedProduct.processor} onChange={handleInputChange} />
                </div>
                <div>
                  <Label htmlFor="coreCount">Core Count</Label>
                  <Input id="coreCount" name="coreCount" type="number" value={editedProduct.coreCount} onChange={handleInputChange} />
                </div>
                <div>
                  <Label htmlFor="memory">Memory</Label>
                  <Input id="memory" name="memory" type="number" value={editedProduct.memory} onChange={handleInputChange} />
                </div>
                <div>
                  <Label htmlFor="operatingSystem">Operating System</Label>
                  <Input id="operatingSystem" name="operatingSystem" value={editedProduct.operatingSystem} onChange={handleInputChange} />
                </div>
                <div className="flex justify-end space-x-4">
                  <Button type="submit">Update</Button>
                  <Button variant="outline" onClick={actions.cancel.productUpdate}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        );
      case DisplayProductState.DisplayingDeleteProductForm:
        return (
          <Card className="mx-auto w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Delete Product: {product.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-4">Are you sure you want to delete this product? This action cannot be undone.</p>
              <form onSubmit={handleDeleteSubmit} className="flex justify-end space-x-4">
                <Button type="submit" variant="destructive">
                  Delete
                </Button>
                <Button variant="outline" onClick={actions.cancel.productUpdate}>
                  Cancel
                </Button>
              </form>
            </CardContent>
          </Card>
        );
      case DisplayProductState.UpdatingProduct:
      case DisplayProductState.DeletingProduct:
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

export default ProductDetail;
