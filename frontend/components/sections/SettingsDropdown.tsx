import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AppContextActions, AppContextData } from "@/context/appContext";
import { ARCHITECTURE_VALUES, HISTORY_MANAGEMENT_VALUES, MODEL_VALUES } from "@/machines/appMachine";
import { SettingsIcon } from "lucide-react";

interface SettingsDropdownProps {
  data: AppContextData;
  actions: AppContextActions;
}

const SettingsDropdown: React.FC<SettingsDropdownProps> = ({ data, actions }) => {
  const handleSettingsChange = (type: string, value: string) => {
    actions.submit.updateSetting({ ...data, [type]: value });
  };
  const handleOpenChange = (open: boolean) => {
    if (open) {
      actions.click.updateSetting();
    } else {
      actions.cancel.updateSetting();
    }
  };

  return (
    <DropdownMenu onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="overflow-hidden rounded-full">
          <SettingsIcon className="h-6 w-6" />
          <span className="sr-only">Settings</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Settings</DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuRadioGroup value={data.model} onValueChange={(value) => handleSettingsChange("model", value)}>
          <DropdownMenuLabel className="font-normal">Model Selection</DropdownMenuLabel>
          {MODEL_VALUES.map((modelType, index) => {
            return (
              <DropdownMenuRadioItem key={index} value={modelType}>
                {modelType}
              </DropdownMenuRadioItem>
            );
          })}
        </DropdownMenuRadioGroup>
        <DropdownMenuSeparator />

        <DropdownMenuRadioGroup value={data.architecture} onValueChange={(value) => handleSettingsChange("architecture", value)}>
          <DropdownMenuLabel className="font-normal">Architecture Selection</DropdownMenuLabel>
          {ARCHITECTURE_VALUES.map((architectureType, index) => {
            return (
              <DropdownMenuRadioItem key={index} value={architectureType}>
                {architectureType}
              </DropdownMenuRadioItem>
            );
          })}
        </DropdownMenuRadioGroup>
        <DropdownMenuSeparator />

        <DropdownMenuRadioGroup value={data.historyManagement} onValueChange={(value) => handleSettingsChange("historyManagement", value)}>
          <DropdownMenuLabel className="font-normal">History Management</DropdownMenuLabel>
          {HISTORY_MANAGEMENT_VALUES.map((historyManagementType, index) => {
            return (
              <DropdownMenuRadioItem key={index} value={historyManagementType}>
                {historyManagementType}
              </DropdownMenuRadioItem>
            );
          })}
        </DropdownMenuRadioGroup>
        <DropdownMenuSeparator />

        <DropdownMenuLabel asChild>
          <Button variant="ghost" className="w-full justify-start" onClick={actions.submit.resetSettings}>
            Reset to Default
          </Button>
        </DropdownMenuLabel>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SettingsDropdown;
