import React from "react";
import { Badge } from "@/components/ui/badge";

type Row = { term: string; in_resume: boolean; occurrences: number };

export default function HeatmapTable({ rows }: { rows: Row[] }) {
  if (!rows?.length) return null;
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="min-w-full text-sm">
        <thead className="bg-muted/40">
          <tr>
            <th className="text-left p-2">Term</th>
            <th className="text-left p-2">Status</th>
            <th className="text-left p-2">Occurrences</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.term + i} className="border-t">
              <td className="p-2">{r.term}</td>
              <td className="p-2">
                {r.in_resume ? (
                  <Badge variant="outline" className="border-green-500/50 text-green-700">Present</Badge>
                ) : (
                  <Badge variant="secondary" className="bg-amber-100 text-amber-900">Missing</Badge>
                )}
              </td>
              <td className="p-2">{r.occurrences}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
