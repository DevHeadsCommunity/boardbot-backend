import { AppContext } from "@/context/appContext";
import { useToast } from "@/hooks/useToast";


export const useProductContext = () => {
  const state = AppContext.useSelector((state) => state);
  const productActorRef = AppContext.useActorRef();
  useToast(productActorRef);

}

