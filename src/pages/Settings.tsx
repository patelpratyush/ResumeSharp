import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, } from "@/components/ui/alert-dialog";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const { toast } = useToast();
  
  const [isLoading, setIsLoading] = useState(true);
  const [confirm, setConfirm] = useState(false);
  const [localSettings, setLocalSettings] = useState({
    dataRetentionDays: 30,
    emailNotifications: true,
    maxWordsPerBullet: 25,
    autoSaveAnalyses: true,
  });

  // Load settings from localStorage
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem('user-settings');
      if (savedSettings) {
        setLocalSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save settings to localStorage
  const saveSettings = (newSettings: typeof localSettings) => {
    try {
      localStorage.setItem('user-settings', JSON.stringify(newSettings));
      setLocalSettings(newSettings);
      toast({
        title: "Settings saved",
        description: "Your preferences have been updated.",
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast({
        title: "Error",
        description: "Failed to save settings. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Clear all localStorage data
  const clearAllData = () => {
    try {
      localStorage.removeItem('analysis-history');
      localStorage.removeItem('user-settings');
      localStorage.clear(); // Clear everything else too
      setConfirm(false);
      toast({
        title: "Data cleared",
        description: "All local data has been removed.",
      });
      // Reset settings to defaults
      setLocalSettings({
        dataRetentionDays: 30,
        emailNotifications: true,
        maxWordsPerBullet: 25,
        autoSaveAnalyses: true,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to clear data. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container py-8 animate-fade-in space-y-6">
      <Helmet>
        <title>Settings – Resume Tailor</title>
        <meta name="description" content="Manage profile, billing, usage, and data retention settings." />
        <link rel="canonical" href="/settings" />
      </Helmet>

      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-2 p-6 md:p-8">
            {isLoading ? (
              <>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Email:</span>
                  <Skeleton className="h-4 w-40" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Plan:</span>
                  <Skeleton className="h-5 w-16" />
                </div>
              </>
            ) : (
              <>
                <div className="text-sm">Plan: <Badge variant="secondary">Free</Badge></div>
                <div className="text-xs text-muted-foreground">
                  Local storage mode - no user account required
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Billing section removed - not applicable in local mode */}

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Usage</CardTitle></CardHeader>
          <CardContent className="p-6 md:p-8">
            {isLoading ? (
              <>
                <Skeleton className="h-4 w-32 mb-2" />
                <Skeleton className="h-2 w-full mb-2" />
                <Skeleton className="h-3 w-20" />
              </>
            ) : (
              <>
                <div className="text-sm mb-1">API Calls</div>
                <div className="text-xs text-muted-foreground mt-2">
                  No limits in local mode
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
          <CardContent className="space-y-4 p-6 md:p-8">
            {isLoading ? (
              <>
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-6 w-12" />
                </div>
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-6 w-12" />
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <Label htmlFor="emailNotifications">Email notifications</Label>
                  <Switch 
                    id="emailNotifications"
                    checked={localSettings.emailNotifications}
                    onCheckedChange={(checked) => setLocalSettings(prev => ({ ...prev, emailNotifications: checked }))}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <Label htmlFor="autoSave">Auto-save analyses</Label>
                  <Switch 
                    id="autoSave"
                    checked={localSettings.autoSaveAnalyses}
                    onCheckedChange={(checked) => setLocalSettings(prev => ({ ...prev, autoSaveAnalyses: checked }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="maxWords">Max words per bullet point</Label>
                  <Input
                    id="maxWords"
                    type="number"
                    min="15"
                    max="50"
                    value={localSettings.maxWordsPerBullet}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, maxWordsPerBullet: parseInt(e.target.value) || 25 }))}
                    className="w-20"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="retention">Data retention (days)</Label>
                  <Input
                    id="retention"
                    type="number"
                    min="7"
                    max="365"
                    value={localSettings.dataRetentionDays}
                    onChange={(e) => setLocalSettings(prev => ({ ...prev, dataRetentionDays: parseInt(e.target.value) || 30 }))}
                    className="w-20"
                  />
                </div>
                
                <Button 
                  onClick={() => saveSettings(localSettings)} 
                  className="w-full mt-4"
                >
                  Save Preferences
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Data Management</CardTitle></CardHeader>
          <CardContent className="space-y-4 p-6 md:p-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-red-600">Clear local data</div>
                <div className="text-sm text-muted-foreground">Remove all analysis history and settings from this browser</div>
              </div>
              <Button variant="destructive" className="hover-scale" onClick={() => setConfirm(true)}>
                Clear Data
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear all data?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all analysis history, settings, and other data stored in your browser. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={clearAllData}>Clear Data</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
