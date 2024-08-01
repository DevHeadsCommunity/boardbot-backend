import { useAppContext } from "@/context/appContext";
import { useToast } from "@/hooks/useToast";

export const useProductContext = () => {
  const { actorRef } = useAppContext();

  const productActorRef = actorRef.product;
  useToast(productActorRef);
};
