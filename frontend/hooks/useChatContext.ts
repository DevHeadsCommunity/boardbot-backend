import { AppContext } from "@/context/appContext";
import { useToast } from "@/hooks/useToast";


export const useChatContext = () => {
  const state = AppContext.useSelector((state) => state);
  const chatActorRef = AppContext.useActorRef();
  useToast(chatActorRef);

}

