import { Helmet } from "react-helmet-async";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, } from "@/components/ui/alert-dialog";
import { useState } from "react";

export default function Settings() {
  const [retention, setRetention] = useState(true);
  const [confirm, setConfirm] = useState(false);

  const onUpgrade = () => console.log("upgrade");
  const onDowngrade = () => console.log("downgrade");
  const onManageBilling = () => console.log("manage billing");
  const onDeleteAccount = () => { setConfirm(false); console.log("delete account"); };

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
            <div className="text-sm">Email: <span className="font-medium">user@example.com</span></div>
            <div className="text-sm">Plan: <Badge variant="secondary">Free</Badge></div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Billing</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2 p-6 md:p-8">
            <Button onClick={onUpgrade} className="hover-scale">Upgrade</Button>
            <Button variant="outline" onClick={onDowngrade} className="hover-scale">Downgrade</Button>
            <Button variant="secondary" onClick={onManageBilling} className="hover-scale">Manage Billing</Button>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Usage</CardTitle></CardHeader>
          <CardContent className="p-6 md:p-8">
            <div className="text-sm mb-1">Monthly resumes</div>
            <Progress value={32} />
            <div className="text-xs text-muted-foreground mt-2">3 / 10 used</div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Data Retention</CardTitle></CardHeader>
          <CardContent className="flex items-center gap-3 p-6 md:p-8">
            <Switch id="retention" checked={retention} onCheckedChange={setRetention} />
            <Label htmlFor="retention">Keep data for 30 days</Label>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 rounded-2xl shadow-soft gradient-border">
          <CardHeader><CardTitle>Danger Zone</CardTitle></CardHeader>
          <CardContent className="p-6 md:p-8">
            <Button variant="destructive" className="hover-scale" onClick={() => setConfirm(true)}>Delete account</Button>
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete account?</AlertDialogTitle>
            <AlertDialogDescription>
              This action is irreversible. All your data and versions will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={onDeleteAccount}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
