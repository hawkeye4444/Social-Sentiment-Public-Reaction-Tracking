/* eslint-disable react-hooks/rules-of-hooks */
"use client";
import useSWR from "swr";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush,
} from "recharts";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Page() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const { data: series } = useSWR(`${base}/series/reddit`, fetcher);
  const { data: shifts } = useSWR(`${base}/shifts/reddit`, fetcher);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Mood Timeline (Reddit)</h1>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={series || []}>
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopOpacity={0.8} />
                <stop offset="95%" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="ts" hide />
            <YAxis domain={[-1, 1]} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="sentiment_mean"
              fillOpacity={1}
              fill="url(#g)"
              strokeOpacity={1}
            />
            <Brush dataKey="ts" height={20} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <h2 className="text-xl font-semibold">Detected Shifts</h2>
      <ul className="list-disc pl-6">
        {(shifts || []).map((s: any, i: number) => (
          <li key={i}>
            <span className="font-mono">{s.ts}</span> — {s.explanation} (score {Number(s.score).toFixed(2)})
          </li>
        ))}
      </ul>
    </div>
  );
}
