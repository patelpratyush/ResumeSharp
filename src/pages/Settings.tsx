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
    <div className="container py-6 space-y-6">
      <Helmet>
        <title>Settings – Resume Tailor</title>
        <meta name="description" content="Manage profile, billing, usage, and data retention settings." />
        <link rel="canonical" href="/settings" />
      </Helmet>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="text-sm">Email: <span className="font-medium">user@example.com</span></div>
            <div className="text-sm">Plan: <Badge variant="secondary">Free</Badge></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Billing</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button onClick={onUpgrade}>Upgrade</Button>
            <Button variant="outline" onClick={onDowngrade}>Downgrade</Button>
            <Button variant="secondary" onClick={onManageBilling}>Manage Billing</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Usage</CardTitle></CardHeader>
          <CardContent>
            <div className="text-sm mb-1">Monthly resumes</div>
            <Progress value={32} />
            <div className="text-xs text-muted-foreground mt-2">3 / 10 used</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Data Retention</CardTitle></CardHeader>
          <CardContent className="flex items-center gap-3">
            <Switch id="retention" checked={retention} onCheckedChange={setRetention} />
            <Label htmlFor="retention">Keep data for 30 days</Label>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Danger Zone</CardTitle></CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={() => setConfirm(true)}>Delete account</Button>
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
