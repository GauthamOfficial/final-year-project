"use client";

import {
  Bar,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export type MonthlySeasonalRow = {
  month: number;
  month_name: string;
  crowd_index: number;
  weather_rating: number;
  is_peak_season: boolean;
  visitor_note: string;
};

type SeasonalChartProps = {
  monthly_data: MonthlySeasonalRow[];
  best_months_names: string[];
};

export function SeasonalChart({
  monthly_data,
  best_months_names,
}: SeasonalChartProps) {
  const chartData = monthly_data.map((r) => ({
    ...r,
    crowd_index: Number(r.crowd_index),
    weather_rating: Number(r.weather_rating),
  }));

  const hint =
    best_months_names.length > 0
      ? best_months_names.join(", ")
      : "See monthly breakdown below";

  return (
    <Card className="overflow-hidden py-0">
      <CardHeader className="space-y-2 pb-2 pt-4">
        <p className="text-sm font-medium">When to visit</p>
        <p className="rounded-lg border border-emerald-200/80 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-900">
          Best months to visit: {hint}
        </p>
      </CardHeader>
      <CardContent className="pb-4 pt-0">
        <div className="h-[220px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
            >
              <XAxis
                dataKey="month_name"
                tick={{ fontSize: 10 }}
                interval={0}
                angle={-35}
                textAnchor="end"
                height={48}
              />
              <YAxis
                yAxisId="left"
                domain={[0, 10]}
                width={32}
                tick={{ fontSize: 10 }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[0, 5]}
                width={28}
                tick={{ fontSize: 10 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const row = payload[0]?.payload as MonthlySeasonalRow | undefined;
                  if (!row) return null;
                  return (
                    <div className="rounded-md border bg-popover px-3 py-2 text-xs shadow-md">
                      <p className="font-semibold text-popover-foreground">
                        {row.month_name}
                      </p>
                      <p className="text-muted-foreground">
                        Crowd: {Number(row.crowd_index).toFixed(1)} / 10
                      </p>
                      <p className="text-muted-foreground">
                        Weather: {row.weather_rating} / 5
                      </p>
                      {row.visitor_note ? (
                        <p className="mt-1 text-muted-foreground">
                          {row.visitor_note}
                        </p>
                      ) : null}
                    </div>
                  );
                }}
              />
              <Bar yAxisId="left" dataKey="crowd_index" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`c-${index}`}
                    fill={entry.is_peak_season ? "#f59e0b" : "#3b82f6"}
                  />
                ))}
              </Bar>
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="weather_rating"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 3, fill: "#22c55e" }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
