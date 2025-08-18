import React, { useEffect, useMemo, useState } from "react";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerTrigger, DrawerFooter } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import DiffText from "./DiffText";
import { apiRewrite } from "@/lib/api";

type Props = {
  analysisId: string;
  jdKeywords: string[];
  bullet: string;
  onAccept: (rewritten: string) => void;
  /** NEW: open programmatically on mount/prop change */
  initialOpen?: boolean;
  /** NEW: append keywords for one-off rewrites (e.g., clicked missing term) */
  extraKeywords?: string[];
  /** optional close callback (used by quick rewrite) */
  onClose?: () => void;
};

export default function RewriteDrawer({ analysisId, jdKeywords, bullet, onAccept, initialOpen, extraKeywords, onClose }: Props) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState(bullet);
  const [loading, setLoading] = useState(false);
  const [out, setOut] = useState<{ rewritten: string; diff: any[] } | null>(null);

  // NEW: honor initialOpen prop
  useEffect(() => { if (initialOpen) setOpen(true); }, [initialOpen]);

  // NEW: combined keywords
  const combinedKeywords = useMemo(
    () => Array.from(new Set([...(jdKeywords || []), ...((extraKeywords ?? []))])),
    [jdKeywords, extraKeywords]
  );

  const run = async () => {
    setLoading(true);
    try {
      const resp = await apiRewrite(analysisId, "experience", text, combinedKeywords, 22);
      setOut(resp);
    } finally {
      setLoading(false);
    }
  };

  const accept = () => {
    if (out?.rewritten) onAccept(out.rewritten);
    setOpen(false);
  };

  return (
    <Drawer
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v && onClose) onClose();
      }}
    >
      <DrawerTrigger asChild>
        <Button variant="outline" size="sm">Rewrite</Button>
      </DrawerTrigger>
      <DrawerContent className="p-4">
        <DrawerHeader>
          <DrawerTitle className="flex items-center gap-2">
            Rewrite Bullet{" "}
            <Badge variant="secondary">
              {combinedKeywords.slice(0, 3).join(", ")}
              {combinedKeywords.length > 3 ? "…" : ""}
            </Badge>
          </DrawerTitle>
        </DrawerHeader>
        <div className="grid gap-3 px-4">
          <Textarea value={text} onChange={e => setText(e.target.value)} rows={3} />
          <div className="flex gap-2">
            <Button onClick={run} disabled={loading}>{loading ? "Rewriting..." : "Run rewrite"}</Button>
            {out?.rewritten && <Button variant="secondary" onClick={accept}>Accept</Button>}
          </div>
          {out && <DiffText original={text} diff={out.diff} />}
        </div>
        <DrawerFooter />
      </DrawerContent>
    </Drawer>
  );
}