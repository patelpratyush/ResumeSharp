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
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { Crown, Trash2, CreditCard, RotateCcw, Users, Calendar, RefreshCw } from "lucide-react";
import type { Tables } from "@/integrations/supabase/types";

type UserProfile = Tables<'user_profiles'>;
type UserSettings = Tables<'user_settings'>;

export default function Settings() {
  const { toast } = useToast();
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(true);
  const [confirm, setConfirm] = useState(false);
  const [deleteAccountConfirm, setDeleteAccountConfirm] = useState(false);
  const [cancelSubConfirm, setCancelSubConfirm] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    email: user?.email || '',
  });
  const [apiUsage, setApiUsage] = useState({
    total_calls: 0,
    calls_this_month: 0,
    last_call_date: null as string | null,
  });
  const [settings, setSettings] = useState({
    dataRetentionDays: 30,
    emailNotifications: true,
    maxWordsPerBullet: 25,
    autoSaveAnalyses: true,
    darkMode: false,
    autoRewrite: false,
    defaultModel: 'gpt-4o-mini',
  });

  // Load user profile and settings from Supabase
  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }

    const loadUserData = async () => {
      try {
        // Load user profile
        const { data: profile, error: profileError } = await supabase
          .from('user_profiles')
          .select('*')
          .eq('id', user.id)
          .single();

        if (profileError && profileError.code !== 'PGRST116') {
          console.error('Failed to load user profile:', profileError);
        } else {
          setUserProfile(profile);
          setProfileForm({
            full_name: profile?.full_name || '',
            email: user?.email || '',
          });
        }

        // Load user settings
        const { data: userSettings, error: settingsError } = await supabase
          .from('user_settings')
          .select('*')
          .eq('user_id', user.id)
          .single();

        if (settingsError && settingsError.code !== 'PGRST116') {
          console.error('Failed to load user settings:', settingsError);
        } else if (userSettings) {
          const settingsData = userSettings.settings as {
            dataRetentionDays?: number;
            emailNotifications?: boolean;
            maxWordsPerBullet?: number;
            autoSaveAnalyses?: boolean;
            darkMode?: boolean;
            autoRewrite?: boolean;
            defaultModel?: string;
          };
          if (settingsData) {
            setSettings(prev => ({ ...prev, ...settingsData }));
          }
        }

        // Load API usage statistics
        const { data: analyses, error: analysesError } = await supabase
          .from('analyses')
          .select('created_at')
          .eq('user_id', user.id);

        if (!analysesError && analyses) {
          const now = new Date();
          const thisMonth = analyses.filter(a => {
            const date = new Date(a.created_at);
            return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
          });
          
          setApiUsage({
            total_calls: analyses.length,
            calls_this_month: thisMonth.length,
            last_call_date: analyses.length > 0 ? analyses[analyses.length - 1].created_at : null,
          });
        }
      } catch (error) {
        console.error('Failed to load user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, [user, navigate]);

  // Save profile changes
  const saveProfile = async () => {
    if (!user) return;

    try {
      const { error } = await supabase
        .from('user_profiles')
        .upsert({
          id: user.id,
          full_name: profileForm.full_name,
          updated_at: new Date().toISOString(),
        });

      if (error) throw error;

      setUserProfile(prev => prev ? { ...prev, full_name: profileForm.full_name } : null);
      setEditingProfile(false);
      toast({
        title: "Profile updated",
        description: "Your profile information has been saved.",
      });
    } catch (error) {
      console.error('Failed to save profile:', error);
      toast({
        title: "Error",
        description: "Failed to save profile. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Upgrade/manage plan
  const upgradePlan = async () => {
    if (!user) return;

    try {
      if (userProfile?.subscription_tier === 'Free') {
        // Redirect to pricing page for upgrades
        navigate('/pricing');
      } else {
        // Open Stripe customer portal for existing subscribers
        const { subscriptionAPI } = await import('@/lib/subscription');
        const { portal_url } = await subscriptionAPI.createCustomerPortal();
        window.open(portal_url, '_blank');
      }
    } catch (error) {
      console.error('Error managing subscription:', error);
      toast({
        title: "Error",
        description: "Failed to open subscription management. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Cancel subscription
  const cancelSubscription = async () => {
    if (!user) return;

    try {
      const { subscriptionAPI } = await import('@/lib/subscription');
      await subscriptionAPI.cancelSubscription();
      
      setCancelSubConfirm(false);
      toast({
        title: "Subscription Cancelled",
        description: "Your subscription will be cancelled at the end of your billing period.",
      });
      
      // Reload user data to reflect changes
      window.location.reload();
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      toast({
        title: "Error",
        description: "Failed to cancel subscription. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Delete account
  const deleteAccount = async () => {
    if (!user) return;

    try {
      // Clear all user data first
      await clearAllData();
      
      // Delete user profile
      await supabase
        .from('user_profiles')
        .delete()
        .eq('id', user.id);

      setDeleteAccountConfirm(false);
      toast({
        title: "Account deleted",
        description: "Your account and all data have been permanently deleted.",
      });
      
      // Sign out and redirect
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Failed to delete account:', error);
      toast({
        title: "Error",
        description: "Failed to delete account. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Clear specific data types
  const clearHistory = async () => {
    if (!user) return;

    try {
      await supabase
        .from('analyses')
        .delete()
        .eq('user_id', user.id);

      toast({
        title: "History cleared",
        description: "All analysis history has been removed.",
      });
    } catch (error) {
      console.error('Failed to clear history:', error);
      toast({
        title: "Error",
        description: "Failed to clear history. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Save settings to Supabase
  const saveSettings = async (newSettings: typeof settings) => {
    if (!user) return;

    try {
      const { error } = await supabase
        .from('user_settings')
        .upsert({
          user_id: user.id,
          settings: newSettings,
          updated_at: new Date().toISOString(),
        });

      if (error) {
        throw error;
      }

      setSettings(newSettings);
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

  // Clear all user data from Supabase
  const clearAllData = async () => {
    if (!user) return;

    try {
      // Delete user's analyses
      await supabase
        .from('analyses')
        .delete()
        .eq('user_id', user.id);

      // Delete user's resumes
      await supabase
        .from('resumes')
        .delete()
        .eq('user_id', user.id);

      // Delete user's rewrite history
      await supabase
        .from('rewrite_history')
        .delete()
        .eq('user_id', user.id);

      // Delete user settings
      await supabase
        .from('user_settings')
        .delete()
        .eq('user_id', user.id);

      setConfirm(false);
      toast({
        title: "Data cleared",
        description: "All your data has been removed.",
      });
      
      // Reset settings to defaults
      setSettings({
        dataRetentionDays: 30,
        emailNotifications: true,
        maxWordsPerBullet: 25,
        autoSaveAnalyses: true,
      });
    } catch (error) {
      console.error('Failed to clear data:', error);
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
        <title>Settings – ResumeSharp</title>
        <meta name="description" content="Manage profile, billing, usage, and data retention settings." />
        <link rel="canonical" href="/settings" />
      </Helmet>

      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Profile</CardTitle>
              {!editingProfile && (
                <Button variant="outline" size="sm" onClick={() => setEditingProfile(true)}>
                  Edit
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 p-6 md:p-8">
            {isLoading ? (
              <>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Name:</span>
                  <Skeleton className="h-4 w-40" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Email:</span>
                  <Skeleton className="h-4 w-40" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Plan:</span>
                  <Skeleton className="h-5 w-16" />
                </div>
              </>
            ) : editingProfile ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input
                    id="fullName"
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm(prev => ({ ...prev, full_name: e.target.value }))}
                    placeholder="Enter your full name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    value={profileForm.email}
                    disabled
                    className="bg-muted"
                  />
                  <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                </div>
                <div className="flex gap-2">
                  <Button onClick={saveProfile} size="sm">Save</Button>
                  <Button variant="outline" size="sm" onClick={() => {
                    setEditingProfile(false);
                    setProfileForm({
                      full_name: userProfile?.full_name || '',
                      email: user?.email || '',
                    });
                  }}>
                    Cancel
                  </Button>
                </div>
              </>
            ) : (
              <>
                <div className="text-sm">Name: <span className="font-medium">{userProfile?.full_name || 'Not set'}</span></div>
                <div className="text-sm">Email: <span className="font-medium">{user?.email}</span></div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Plan:</span>
                  <Badge variant={userProfile?.subscription_tier === 'Free' ? 'secondary' : 'default'} className="flex items-center gap-1">
                    {userProfile?.subscription_tier !== 'Free' && <Crown className="w-3 h-3" />}
                    {userProfile?.subscription_tier || 'Free'}
                  </Badge>
                </div>
                <Button variant="outline" size="sm" onClick={signOut} className="mt-2">
                  Sign Out
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Billing section removed - not applicable in local mode */}

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>API Usage</CardTitle>
              <RefreshCw className="w-4 h-4 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent className="p-6 md:p-8 space-y-4">
            {isLoading ? (
              <>
                <Skeleton className="h-4 w-32 mb-2" />
                <Skeleton className="h-2 w-full mb-2" />
                <Skeleton className="h-3 w-20" />
              </>
            ) : (
              <>
                <div>
                  <div className="text-sm mb-1">Monthly Usage</div>
                  <Progress 
                    value={userProfile ? Math.min((apiUsage.calls_this_month || 0) / (userProfile.api_calls_limit || 100) * 100, 100) : 0} 
                    className="mb-2" 
                  />
                  <div className="text-xs text-muted-foreground">
                    {apiUsage.calls_this_month || 0} / {userProfile?.api_calls_limit || 100} calls this month
                  </div>
                </div>
                
                <Separator />
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Total Calls</div>
                    <div className="font-medium">{apiUsage.total_calls}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">This Month</div>
                    <div className="font-medium">{apiUsage.calls_this_month}</div>
                  </div>
                </div>
                
                {apiUsage.last_call_date && (
                  <div className="text-xs text-muted-foreground">
                    Last call: {new Date(apiUsage.last_call_date).toLocaleDateString()}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
          <CardContent className="space-y-6 p-6 md:p-8">
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-medium">General</h3>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="emailNotifications">Email notifications</Label>
                      <Switch 
                        id="emailNotifications"
                        checked={settings.emailNotifications}
                        onCheckedChange={(checked) => setSettings(prev => ({ ...prev, emailNotifications: checked }))}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <Label htmlFor="autoSave">Auto-save analyses</Label>
                      <Switch 
                        id="autoSave"
                        checked={settings.autoSaveAnalyses}
                        onCheckedChange={(checked) => setSettings(prev => ({ ...prev, autoSaveAnalyses: checked }))}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="autoRewrite">Auto-rewrite suggestions</Label>
                      <Switch 
                        id="autoRewrite"
                        checked={settings.autoRewrite}
                        onCheckedChange={(checked) => setSettings(prev => ({ ...prev, autoRewrite: checked }))}
                      />
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-medium">AI Settings</h3>
                    
                    <div className="space-y-2">
                      <Label htmlFor="defaultModel">Default AI Model</Label>
                      <select
                        id="defaultModel"
                        value={settings.defaultModel}
                        onChange={(e) => setSettings(prev => ({ ...prev, defaultModel: e.target.value }))}
                        className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
                      >
                        <option value="gpt-4o-mini">GPT-4o Mini (Fast)</option>
                        <option value="gpt-4o">GPT-4o (Balanced)</option>
                        <option value="gpt-4">GPT-4 (Precise)</option>
                      </select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="maxWords">Max words per bullet point</Label>
                      <Input
                        id="maxWords"
                        type="number"
                        min="15"
                        max="50"
                        value={settings.maxWordsPerBullet}
                        onChange={(e) => setSettings(prev => ({ ...prev, maxWordsPerBullet: parseInt(e.target.value) || 25 }))}
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
                        value={settings.dataRetentionDays}
                        onChange={(e) => setSettings(prev => ({ ...prev, dataRetentionDays: parseInt(e.target.value) || 30 }))}
                        className="w-20"
                      />
                    </div>
                  </div>
                </div>
                
                <Button 
                  onClick={() => saveSettings(settings)} 
                  className="w-full mt-6"
                >
                  Save Preferences
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Plan Management */}
        <Card className="lg:col-span-2 rounded-2xl shadow-soft gradient-border">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-amber-500" />
              <CardTitle>Plan & Billing</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-6 md:p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Current Plan</div>
                <div className="font-semibold text-lg">{userProfile?.subscription_tier || 'Free'}</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Monthly Limit</div>
                <div className="font-semibold text-lg">{userProfile?.api_calls_limit || 100}</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Used This Month</div>
                <div className="font-semibold text-lg">{apiUsage.calls_this_month || 0}</div>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-3">
              {userProfile?.subscription_tier === 'Free' ? (
                <Button onClick={upgradePlan} className="flex items-center gap-2">
                  <Crown className="w-4 h-4" />
                  Upgrade Plan
                </Button>
              ) : (
                <>
                  <Button onClick={upgradePlan} variant="outline" className="flex items-center gap-2">
                    <CreditCard className="w-4 h-4" />
                    Manage Billing
                  </Button>
                  <Button 
                    onClick={() => setCancelSubConfirm(true)} 
                    variant="outline" 
                    className="text-red-600 hover:text-red-700"
                  >
                    Cancel Subscription
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card className="lg:col-span-2 rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Data Management</CardTitle></CardHeader>
          <CardContent className="space-y-6 p-6 md:p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="font-medium">Clear Specific Data</h3>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Analysis History</div>
                    <div className="text-sm text-muted-foreground">Remove all analysis results and comparisons</div>
                  </div>
                  <Button variant="outline" size="sm" onClick={clearHistory} className="flex items-center gap-2">
                    <RotateCcw className="w-3 h-3" />
                    Clear
                  </Button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-red-600">All Data</div>
                    <div className="text-sm text-muted-foreground">Remove all your data including settings</div>
                  </div>
                  <Button variant="destructive" size="sm" onClick={() => setConfirm(true)} className="flex items-center gap-2">
                    <Trash2 className="w-3 h-3" />
                    Clear All
                  </Button>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium text-red-600">Danger Zone</h3>
                
                <div className="border border-red-200 rounded-lg p-4 space-y-3">
                  <div>
                    <div className="font-medium text-red-600">Delete Account</div>
                    <div className="text-sm text-muted-foreground">Permanently delete your account and all associated data. This action cannot be undone.</div>
                  </div>
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={() => setDeleteAccountConfirm(true)}
                    className="flex items-center gap-2"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Clear All Data Dialog */}
      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear all data?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove all your analysis history, resumes, settings, and other data from your account. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={clearAllData}>Clear Data</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Cancel Subscription Dialog */}
      <AlertDialog open={cancelSubConfirm} onOpenChange={setCancelSubConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel subscription?</AlertDialogTitle>
            <AlertDialogDescription>
              Your subscription will be cancelled and you'll be moved to the free plan at the end of your current billing period. You'll retain access to premium features until then.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
            <AlertDialogAction onClick={cancelSubscription} className="bg-red-600 hover:bg-red-700">
              Cancel Subscription
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Account Dialog */}
      <AlertDialog open={deleteAccountConfirm} onOpenChange={setDeleteAccountConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete account permanently?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete your account and all associated data including analysis history, resumes, settings, and billing information. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={deleteAccount} className="bg-red-600 hover:bg-red-700">
              Delete Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
