import React from "react";
import { Badge } from "@/components/ui/badge";

type ATS = {
  bullets: { count: number; avg_len: number; with_numbers: number };
  passive_ratio: number;
  first_person: boolean;
  contact_present: boolean;
};

export default function ATSChips({ ats, flags }: { ats?: ATS; flags?: string[] }) {
  if (!ats && (!flags || flags.length === 0)) return null;
  return (
    <div className="space-y-2">
      {ats && (
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" title="Total bullets">
            Bullets: {ats.bullets?.count ?? 0}
          </Badge>
          <Badge variant="outline" title="Average words per bullet">
            Avg length: {Math.round((ats.bullets?.avg_len ?? 0) * 10) / 10}
          </Badge>
          <Badge variant="outline" title="Bullets that include numbers/metrics">
            Quantified: {ats.bullets?.with_numbers ?? 0}
          </Badge>
          <Badge variant="outline" title="Estimated passive voice ratio">
            Passive≈ {Math.round((ats.passive_ratio ?? 0) * 100)}%
          </Badge>
          <Badge variant={ats.first_person ? "secondary" : "outline"} title="First-person pronouns">
            {ats.first_person ? "1st person found" : "No 1st person"}
          </Badge>
          <Badge variant={ats.contact_present ? "outline" : "secondary"} title="Contact block present">
            {ats.contact_present ? "Contact OK" : "Contact missing"}
          </Badge>
        </div>
      )}
      {flags && flags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {flags.map((f, i) => (
            <Badge key={i} className="bg-amber-100 text-amber-900" variant="secondary">
              {f}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
