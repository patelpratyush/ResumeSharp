import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/use-toast";
import { Settings, Save, RotateCcw } from "lucide-react";
import { useState, useEffect } from "react";

export type UserSettings = {
  defaultMaxWords: number;
  exportStyle: 'professional' | 'modern' | 'minimal';
  autoSaveHistory: boolean;
  showAdvancedAnalysis: boolean;
  defaultTimeout: number;
};

const DEFAULT_SETTINGS: UserSettings = {
  defaultMaxWords: 22,
  exportStyle: 'professional',
  autoSaveHistory: true,
  showAdvancedAnalysis: false,
  defaultTimeout: 30
};

type SettingsDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  settings: UserSettings;
  onSettingsChange: (settings: UserSettings) => void;
};

export default function SettingsDialog({ 
  open, 
  onOpenChange, 
  settings, 
  onSettingsChange 
}: SettingsDialogProps) {
  const [localSettings, setLocalSettings] = useState<UserSettings>(settings);
  const { toast } = useToast();

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleSave = () => {
    onSettingsChange(localSettings);
    onOpenChange(false);
    toast({
      title: "Settings Saved",
      description: "Your preferences have been updated.",
    });
  };

  const handleReset = () => {
    setLocalSettings(DEFAULT_SETTINGS);
    toast({
      title: "Settings Reset",
      description: "All settings have been reset to defaults.",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Settings & Preferences
          </DialogTitle>
          <DialogDescription>
            Customize your Tailor Flow experience and set default preferences.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Rewrite Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Rewrite Preferences</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="maxWords">Default Max Words per Bullet</Label>
                <Input
                  id="maxWords"
                  type="number"
                  min="15"
                  max="35"
                  value={localSettings.defaultMaxWords}
                  onChange={(e) => setLocalSettings(prev => ({ 
                    ...prev, 
                    defaultMaxWords: parseInt(e.target.value) || 22 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  Recommended: 20-25 words for optimal ATS scanning
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timeout">Analysis Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  min="10"
                  max="60"
                  value={localSettings.defaultTimeout}
                  onChange={(e) => setLocalSettings(prev => ({ 
                    ...prev, 
                    defaultTimeout: parseInt(e.target.value) || 30 
                  }))}
                />
                <p className="text-xs text-muted-foreground">
                  How long to wait for API responses
                </p>
              </div>
            </div>
          </div>

          {/* Export Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Export Preferences</h3>
            
            <div className="space-y-2">
              <Label htmlFor="exportStyle">Default Export Style</Label>
              <Select 
                value={localSettings.exportStyle} 
                onValueChange={(value: 'professional' | 'modern' | 'minimal') => 
                  setLocalSettings(prev => ({ ...prev, exportStyle: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select export style" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">
                    Professional - Traditional format with clear sections
                  </SelectItem>
                  <SelectItem value="modern">
                    Modern - Clean design with better typography  
                  </SelectItem>
                  <SelectItem value="minimal">
                    Minimal - Compact layout, more content per page
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                This affects DOCX and PDF export formatting
              </p>
            </div>
          </div>

          {/* Privacy & Data Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Privacy & Data</h3>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-save Analysis History</Label>
                <p className="text-xs text-muted-foreground">
                  Automatically save your last 10 analyses locally
                </p>
              </div>
              <Switch
                checked={localSettings.autoSaveHistory}
                onCheckedChange={(checked) => 
                  setLocalSettings(prev => ({ ...prev, autoSaveHistory: checked }))
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Show Advanced Analysis Details</Label>
                <p className="text-xs text-muted-foreground">
                  Display detailed scoring breakdowns and debugging info
                </p>
              </div>
              <Switch
                checked={localSettings.showAdvancedAnalysis}
                onCheckedChange={(checked) => 
                  setLocalSettings(prev => ({ ...prev, showAdvancedAnalysis: checked }))
                }
              />
            </div>
          </div>

          {/* Current Settings Summary */}
          <div className="bg-muted p-4 rounded-lg space-y-2">
            <h4 className="font-medium">Current Settings Summary</h4>
            <div className="text-sm text-muted-foreground space-y-1">
              <div>• Default bullet length: {localSettings.defaultMaxWords} words</div>
              <div>• Export style: {localSettings.exportStyle}</div>
              <div>• History auto-save: {localSettings.autoSaveHistory ? 'Enabled' : 'Disabled'}</div>
              <div>• Advanced details: {localSettings.showAdvancedAnalysis ? 'Shown' : 'Hidden'}</div>
              <div>• API timeout: {localSettings.defaultTimeout} seconds</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button onClick={handleSave} className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              Save Settings
            </Button>
            <Button onClick={handleReset} variant="outline">
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { DEFAULT_SETTINGS };