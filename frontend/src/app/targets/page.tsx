"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, EmployeeTarget, User } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function TargetsPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [targets, setTargets] = useState<EmployeeTarget[]>([]);
  const [employees, setEmployees] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ employee_id: "", target_photos: "" });

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getTargets(year, month),
      api.getUsers({ role: "employee", page_size: "100" }),
    ])
      .then(([t, u]) => {
        setTargets(t);
        setEmployees(u.items);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [year, month]);

  const handleSetTarget = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.setEmployeeTarget({
        employee_id: Number(form.employee_id),
        year,
        month,
        target_photos: Number(form.target_photos),
      });
      toast({ title: "Target saved" });
      setForm({ employee_id: "", target_photos: "" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Employee Targets</h1>
          <p className="text-muted-foreground">
            Set monthly photo targets. Commission follows each branch rate before and after target.
          </p>
        </div>

        <div className="grid gap-4 sm:flex sm:flex-wrap">
          <div>
            <Label>Year</Label>
            <Input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} className="w-28" />
          </div>
          <div>
            <Label>Month</Label>
            <select
              className="flex h-10 rounded-md border border-input bg-white px-3 text-sm"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
        </div>

        <Card>
          <CardHeader><CardTitle>Set Monthly Target</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSetTarget} className="grid gap-4 sm:flex sm:flex-wrap sm:items-end">
              <div className="w-full sm:w-auto">
                <Label>Employee</Label>
                <select
                  className="flex h-10 min-w-[200px] rounded-md border border-input bg-white px-3 text-sm"
                  value={form.employee_id}
                  onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                  required
                >
                  <option value="">Select employee</option>
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                  ))}
                </select>
              </div>
              <div className="w-full sm:w-auto">
                <Label>Target (photos/month)</Label>
                <Input
                  type="number"
                  min="1"
                  value={form.target_photos}
                  onChange={(e) => setForm({ ...form, target_photos: e.target.value })}
                  className="w-full sm:w-40"
                  required
                />
              </div>
              <Button type="submit" className="w-full sm:w-auto">Save Target</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Team Progress — {MONTHS[month - 1]} {year}</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
              </div>
            ) : targets.length === 0 ? (
              <p className="p-6 text-muted-foreground">No targets set for this month yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-4 text-left">Employee</th>
                    <th className="p-4 text-left">Printed</th>
                    <th className="p-4 text-left">Target</th>
                    <th className="p-4 text-left">Progress</th>
                    <th className="p-4 text-left">Before Target</th>
                    <th className="p-4 text-left">After Target</th>
                    <th className="p-4 text-left">Total Commission</th>
                  </tr>
                </thead>
                <tbody>
                  {targets.map((t) => (
                    <tr key={t.employee_id} className="border-b">
                      <td className="p-4 font-medium">{t.employee_name}</td>
                      <td className="p-4">{t.photos_printed}</td>
                      <td className="p-4">{t.target_photos || "—"}</td>
                      <td className="p-4">
                        {t.target_photos > 0 ? (
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-24 overflow-hidden rounded-full bg-secondary">
                              <div
                                className="h-full bg-foreground transition-all"
                                style={{ width: `${Math.min(t.progress_percent, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs">{t.progress_percent}%</span>
                            {t.target_met && <span className="text-xs font-medium text-green-600">✓ Met</span>}
                          </div>
                        ) : "—"}
                      </td>
                      <td className="p-4">{formatCurrency(t.base_commission)}</td>
                      <td className="p-4">{formatCurrency(t.bonus_commission)}</td>
                      <td className="p-4 font-semibold">{formatCurrency(t.total_commission)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
