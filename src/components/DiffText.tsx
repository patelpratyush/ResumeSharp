import React from "react";

type DiffOp = { op: string; from: string; to: string };
export default function DiffText({ original, diff }: { original: string; diff: DiffOp[] }) {
  if (!diff?.length) return <span>{original}</span>;
  return (
    <div className="text-sm leading-6">
      <div className="mb-1 font-medium text-muted-foreground">Original</div>
      <p className="rounded-md border p-3">
        {original}
      </p>
      <div className="mt-3 mb-1 font-medium text-muted-foreground">Rewritten</div>
      <p className="rounded-md border p-3">
        {diff.map((d, i) => {
          if (d.op === "delete") return <del key={i} className="opacity-70">{d.from}</del>;
          if (d.op === "insert") return <ins key={i} className="px-1 rounded bg-primary/15">{d.to}</ins>;
          if (d.op === "replace") return (
            <span key={i}>
              <del className="opacity-70">{d.from}</del>
              <ins className="px-1 rounded bg-primary/15">{d.to}</ins>
            </span>
          );
          return <span key={i}>{d.to || d.from}</span>;
        })}
      </p>
    </div>
  );
}
