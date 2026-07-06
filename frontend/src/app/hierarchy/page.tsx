"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { OrgTree } from "@/components/hierarchy/org-tree";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { api, HierarchyData } from "@/lib/api";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function HierarchyPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data, setData] = useState<HierarchyData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getHierarchy(year, month).then(setData).finally(() => setLoading(false));
  }, [year, month]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Team Hierarchy</h1>
          <p className="text-muted-foreground">
            Organization tree — Admin, Managers, and Employees with monthly target progress.
          </p>
        </div>

        <div className="grid gap-4 sm:flex sm:flex-wrap">
          <div>
            <Label>Year</Label>
            <Input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="w-28"
            />
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
          <CardHeader>
            <CardTitle>
              {MONTHS[month - 1]} {year} — Target Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-40 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
              </div>
            ) : data?.tree ? (
              <OrgTree tree={data.tree} />
            ) : (
              <p className="text-muted-foreground">No hierarchy data available.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6 text-sm text-muted-foreground">
            <p><strong>Commission:</strong> Each branch has its own before-target and after-target rate.</p>
            <p className="mt-1">Employees without a target show printed photos only. Set targets in Employee Targets.</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
