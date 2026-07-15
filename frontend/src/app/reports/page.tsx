"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

const reports = [
  { id: "daily", name: "Daily Sales Report" },
  { id: "monthly", name: "Monthly Sales Report" },
  { id: "employee-performance", name: "Employee Performance" },
  { id: "attendance", name: "Attendance Sheet" },
  { id: "manager-performance", name: "Manager Performance" },
  { id: "revenue", name: "Revenue Report (30 days)" },
];

export default function ReportsPage() {
  const download = async (type: string, format: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const path = type === "attendance" ? "/attendance/sheet" : `/reports/${type}`;
      const res = await fetch(`${API_URL}${path}?format=${format}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type}.${format === "excel" ? "xlsx" : format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: "Report downloaded" });
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold sm:text-3xl">Reports</h1>
        <div className="grid gap-4 md:grid-cols-2">
          {reports.map((report) => (
            <Card key={report.id}>
              <CardHeader><CardTitle className="text-lg">{report.name}</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-3 gap-2 sm:flex sm:flex-wrap">
                <Button variant="outline" size="sm" onClick={() => download(report.id, "csv")}>CSV</Button>
                <Button variant="outline" size="sm" onClick={() => download(report.id, "excel")}>Excel</Button>
                <Button variant="outline" size="sm" onClick={() => download(report.id, "pdf")}>PDF</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
