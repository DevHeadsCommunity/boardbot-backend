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
  const handleSettingsChange = (type: keyof AppContextData, value: string) => {
    actions.submit.updateSetting({ ...data, [type]: value });
  };

  const handleOpenChange = (open: boolean) => {
    if (open) {
      actions.click.updateSetting();
    } else {
      actions.cancel.updateSetting();
    }
  };

  const renderRadioGroup = (label: string, currentValue: string, values: readonly string[], settingKey: keyof AppContextData) => (
    <>
      <DropdownMenuRadioGroup value={currentValue} onValueChange={(value) => handleSettingsChange(settingKey, value)}>
        <DropdownMenuLabel className="font-normal">{label}</DropdownMenuLabel>
        {values.map((value) => (
          <DropdownMenuRadioItem key={value} value={value}>
            {value}
          </DropdownMenuRadioItem>
        ))}
      </DropdownMenuRadioGroup>
      <DropdownMenuSeparator />
    </>
  );

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
        {renderRadioGroup("Model Selection", data.model, MODEL_VALUES, "model")}
        {renderRadioGroup("Architecture Selection", data.architecture, ARCHITECTURE_VALUES, "architecture")}
        {renderRadioGroup("History Management", data.historyManagement, HISTORY_MANAGEMENT_VALUES, "historyManagement")}
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
