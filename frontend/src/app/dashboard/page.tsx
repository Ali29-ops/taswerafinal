"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/components/providers/auth-provider";
import { api, DashboardData } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <Card className="border-border shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      </DashboardLayout>
    );
  }

  const stats = data?.stats;
  const role = user?.role;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, {user?.first_name}</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {role === "admin" && (
            <>
              <StatCard title="Total Revenue" value={formatCurrency(stats?.total_revenue || 0)} />
              <StatCard title="Photos Printed" value={stats?.total_photos_printed || 0} />
              <StatCard title="Total Orders" value={stats?.total_sales || 0} />
              <StatCard title="Price/Photo" value={formatCurrency(stats?.print_price_per_photo || 120)} />
            </>
          )}
          {role === "manager" && (
            <>
              <StatCard title="Team Revenue" value={formatCurrency(stats?.team_revenue || 0)} />
              <StatCard title="Team Photos Printed" value={stats?.team_photos_printed || 0} />
              <StatCard title="Team Orders" value={stats?.team_sales || 0} />
              <StatCard title="Price/Photo" value={formatCurrency(stats?.print_price_per_photo || 120)} />
            </>
          )}
          {role === "employee" && (
            <>
              <StatCard title="My Commission" value={formatCurrency(stats?.my_commission || 0)} />
              <StatCard title="Photos Printed" value={stats?.my_photos_printed || 0} />
              <StatCard title="Monthly Target" value={stats?.my_target_photos || "Not set"} />
              <StatCard title="Target Progress" value={stats?.my_target_photos ? `${stats.my_target_progress}%` : "â€”"} />
            </>
          )}
        </div>

        {role === "employee" && (stats?.my_target_photos ?? 0) > 0 && stats && (
          <Card className="border-border shadow-sm">
            <CardHeader>
              <CardTitle>Monthly Target Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>{stats.my_photos_printed} / {stats.my_target_photos} photos</span>
                <span className="font-medium">{stats.my_target_progress}%</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full bg-foreground transition-all"
                  style={{ width: `${Math.min(stats.my_target_progress, 100)}%` }}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Commission is calculated from the branch rate on each sale, with a separate rate after target.
                Your total this month: <strong>{formatCurrency(stats.my_commission)}</strong>
              </p>
            </CardContent>
          </Card>
        )}

        {role === "manager" && data?.employee_targets && data.employee_targets.length > 0 && (
          <Card className="border-border shadow-sm">
            <CardHeader>
              <CardTitle>Team Targets This Month</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-3 text-left">Employee</th>
                    <th className="p-3 text-left">Printed</th>
                    <th className="p-3 text-left">Target</th>
                    <th className="p-3 text-left">Commission</th>
                  </tr>
                </thead>
                <tbody>
                  {data.employee_targets.map((t) => (
                    <tr key={t.employee_id} className="border-b">
                      <td className="p-3">{t.employee_name}</td>
                      <td className="p-3">{t.photos_printed}</td>
                      <td className="p-3">{t.target_photos || "â€”"}</td>
                      <td className="p-3 font-medium">{formatCurrency(t.total_commission)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Revenue (7 days)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data?.revenue_chart || []}>
                  <XAxis dataKey="label" stroke="#a3a3a3" fontSize={12} />
                  <YAxis stroke="#a3a3a3" fontSize={12} />
                  <Tooltip contentStyle={{ background: "#fff", border: "1px solid #e5e5e5", color: "#171717" }} />
                  <Bar dataKey="value" fill="#171717" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Print Orders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data?.recent_sales.length === 0 && (
                  <p className="text-sm text-muted-foreground">No recent sales</p>
                )}
                {data?.recent_sales.map((sale) => (
                  <div key={sale.id} className="flex items-center justify-between border-b border-border pb-2">
                    <div>
                      <p className="font-medium">{sale.customer_name || `Customer #${sale.customer_id}`}</p>
                      <p className="text-xs text-muted-foreground">
                        {sale.photo_count} photos ({sale.small_photo_count} small, {sale.large_photo_count} large) - {formatDate(sale.created_at)}
                      </p>
                    </div>
                    <span className="font-semibold">{formatCurrency(sale.amount)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
