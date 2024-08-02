import { useToast } from "@/hooks/useToast";
import { useAppContext } from "./useAppContext";

export const useProductContext = () => {
  const { actorRef } = useAppContext();

  const productActorRef = actorRef.product;
  useToast(productActorRef);
};
