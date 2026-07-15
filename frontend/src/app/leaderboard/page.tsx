"use client";

import { useEffect, useState } from "react";
import { EyeOff, Medal, Trophy } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, LeaderboardData } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";

function rankStyle(rank: number) {
  if (rank === 1) return "bg-amber-100 text-amber-900";
  if (rank === 2) return "bg-slate-100 text-slate-900";
  if (rank === 3) return "bg-orange-100 text-orange-900";
  return "bg-secondary text-foreground";
}

export default function LeaderboardPage() {
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLeaderboard().then(setData).finally(() => setLoading(false));
  }, []);

  const isBlurred = Boolean(data?.is_blurred);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">Leaderboard</h1>
            <p className="text-muted-foreground">Monthly employee ranking across all branches</p>
          </div>
          {isBlurred && (
            <div className="flex items-center gap-2 rounded-md border bg-white px-3 py-2 text-sm text-muted-foreground">
              <EyeOff className="h-4 w-4" />
              Results are hidden until next month
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              {(data?.entries || []).slice(0, 3).map((entry) => (
                <Card key={entry.rank} className="border-border shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className={cn("flex h-10 w-10 items-center justify-center rounded-full", rankStyle(entry.rank))}>
                        {entry.rank === 1 ? <Trophy className="h-5 w-5" /> : <Medal className="h-5 w-5" />}
                      </div>
                      <span className="text-sm font-medium text-muted-foreground">#{entry.rank}</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <h2 className={cn("text-lg font-semibold", isBlurred && "blur-sm select-none")}>{entry.employee_name}</h2>
                    <p className={cn("text-sm text-muted-foreground", isBlurred && "blur-sm select-none")}>
                      {entry.branch_name || "All branches"}
                    </p>
                    <div className={cn("mt-4 grid grid-cols-2 gap-3 text-sm", isBlurred && "blur-sm select-none")}>
                      <div>
                        <p className="text-muted-foreground">Photos</p>
                        <p className="font-semibold">{entry.photos_printed}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Commission</p>
                        <p className="font-semibold">{formatCurrency(entry.total_commission)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="border-border shadow-sm">
              <CardHeader>
                <CardTitle>{data?.month}/{data?.year} Ranking</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-secondary/60">
                        <th className="p-3 text-left">Rank</th>
                        <th className="p-3 text-left">Employee</th>
                        <th className="p-3 text-left">Branch</th>
                        <th className="p-3 text-right">Photos</th>
                        <th className="p-3 text-right">Target</th>
                        <th className="p-3 text-right">Progress</th>
                        <th className="p-3 text-right">Commission</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data?.entries.map((entry) => (
                        <tr key={entry.rank} className="border-b">
                          <td className="p-3 font-semibold">#{entry.rank}</td>
                          <td className={cn("p-3 font-medium", isBlurred && "blur-sm select-none")}>{entry.employee_name}</td>
                          <td className={cn("p-3 text-muted-foreground", isBlurred && "blur-sm select-none")}>{entry.branch_name || "-"}</td>
                          <td className={cn("p-3 text-right", isBlurred && "blur-sm select-none")}>{entry.photos_printed}</td>
                          <td className={cn("p-3 text-right", isBlurred && "blur-sm select-none")}>{entry.target_photos || "-"}</td>
                          <td className={cn("p-3 text-right", isBlurred && "blur-sm select-none")}>{entry.progress_percent}%</td>
                          <td className={cn("p-3 text-right font-medium", isBlurred && "blur-sm select-none")}>
                            {formatCurrency(entry.total_commission)}
                          </td>
                        </tr>
                      ))}
                      {data?.entries.length === 0 && (
                        <tr>
                          <td className="p-6 text-center text-muted-foreground" colSpan={7}>No employees yet</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
