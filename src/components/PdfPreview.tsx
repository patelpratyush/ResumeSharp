import { Card, CardContent } from "@/components/ui/card";

type PdfPreviewProps = {
  file?: File | null;
};

export default function PdfPreview({ file }: PdfPreviewProps) {
  return (
    <Card aria-live="polite">
      <CardContent className="h-64 flex items-center justify-center text-sm text-muted-foreground">
        {file ? `Preview unavailable in stub: ${file.name}` : "No file selected"}
      </CardContent>
    </Card>
  );
}
