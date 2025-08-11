import { Card, CardContent } from "@/components/ui/card";

type PdfPreviewProps = {
  file?: File | null;
};

export default function PdfPreview({ file }: PdfPreviewProps) {
  return (
    <Card aria-live="polite" className="rounded-xl">
      <CardContent className="h-64 flex items-center justify-center text-sm text-muted-foreground">
        {file ? (
          `Preview unavailable in stub: ${file.name}`
        ) : (
          <div className="flex flex-col items-center gap-2 animate-fade-in" aria-label="No file selected">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="text-muted-foreground">
              <path d="M7 3h6l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M13 3v4h4" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
            <span>No file selected</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
