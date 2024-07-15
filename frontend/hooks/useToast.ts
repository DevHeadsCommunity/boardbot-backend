import { useCallback, useEffect } from "react";
import { ToastOptions, toast } from "react-toastify";

interface ToastConfig {
  position?: ToastOptions["position"];
  autoClose?: ToastOptions["autoClose"];
  hideProgressBar?: ToastOptions["hideProgressBar"];
  closeOnClick?: ToastOptions["closeOnClick"];
  pauseOnHover?: ToastOptions["pauseOnHover"];
  draggable?: ToastOptions["draggable"];
  progress?: ToastOptions["progress"];
}

export type ToastType = "success" | "error" | "info" | "warning";

export const useToast = (actorRef: any, config: ToastConfig = {}) => {
  const showToast = useCallback(
    (type: ToastType, message: string) => {
      toast(message, {
        position: config.position || "bottom-right",
        autoClose: config.autoClose || 3000,
        hideProgressBar: config.hideProgressBar || false,
        closeOnClick: config.closeOnClick || false,
        pauseOnHover: config.pauseOnHover || true,
        draggable: config.draggable || true,
        progress: config.progress || undefined,
        type,
      });
    },
    [config]
  );

  useEffect(() => {
    if (!actorRef) {
      return;
    }
    const sub = actorRef.on("notification", (event: { data: { type: ToastType; message: string } }) => {
      showToast(event.data.type, event.data.message);
    });

    return () => {
      sub.unsubscribe();
    };
  }, [actorRef, showToast]);

  return;
};
