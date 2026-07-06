"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock, Download } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { api, AttendanceRecord, User } from "@/lib/api";
import { formatDate } from "@/lib/utils";

function formatTime(value?: string) {
  if (!value) return "-";
  return new Date(value).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDuration(minutes?: number) {
  if (minutes == null) return "-";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (!hours) return `${mins}m`;
  return `${hours}h ${mins}m`;
}

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const { user } = useAuth();
  const isEmployee = user?.role === "employee";
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [employees, setEmployees] = useState<User[]>([]);
  const [partners, setPartners] = useState<User[]>([]);
  const [partnerId, setPartnerId] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [filters, setFilters] = useState({
    start_date: todayInputValue(),
    end_date: todayInputValue(),
    employee_id: "",
  });

  const sheetParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    if (filters.employee_id) params.employee_id = filters.employee_id;
    return params;
  }, [filters]);

  const load = async () => {
    setLoading(true);
    try {
      if (isEmployee) {
        const [today, partnerOptions] = await Promise.all([
          api.getMyAttendanceToday(),
          api.getAttendancePartners(),
        ]);
        setTodayRecord(today);
        setPartners(partnerOptions);
        setPartnerId(today?.partner_employee_id ? String(today.partner_employee_id) : "");
      } else {
        const [attendance, users] = await Promise.all([
          api.getAttendance(sheetParams),
          api.getUsers({ role: "employee", page_size: "100" }),
        ]);
        setRecords(attendance);
        setEmployees(users.items);
      }
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to load attendance",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) load();
  }, [user, isEmployee, sheetParams]);

  const handleCheckIn = async () => {
    setSubmitting(true);
    try {
      setTodayRecord(await api.checkIn());
      toast({ title: "Checked in" });
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheckOut = async () => {
    setSubmitting(true);
    try {
      setTodayRecord(await api.checkOut(partnerId ? Number(partnerId) : undefined));
      toast({ title: "Checked out" });
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    } finally {
      setSubmitting(false);
    }
  };

  const download = async (format: string) => {
    try {
      const res = await api.getAttendanceSheet(format, sheetParams);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `attendance.${format === "excel" ? "xlsx" : format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: "Attendance sheet downloaded" });
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Attendance</h1>
          <p className="text-muted-foreground">
            {isEmployee ? "Check in when your shift starts and check out when you leave." : "Review employee check-in and check-out timings."}
          </p>
        </div>

        {isEmployee ? (
          <Card className="max-w-xl border-border shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Today
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {loading ? (
                <div className="h-24 animate-pulse rounded-md bg-secondary" />
              ) : (
                <>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Check in</p>
                      <p className="text-lg font-semibold">{formatTime(todayRecord?.check_in_at)}</p>
                    </div>
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Check out</p>
                      <p className="text-lg font-semibold">{formatTime(todayRecord?.check_out_at)}</p>
                    </div>
                    <div className="rounded-md border border-border p-3">
                      <p className="text-xs text-muted-foreground">Total</p>
                      <p className="text-lg font-semibold">{formatDuration(todayRecord?.total_minutes)}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shift-partner">Shift partner (optional)</Label>
                    <select
                      id="shift-partner"
                      className="flex h-10 w-full rounded-md border border-input bg-white px-3 text-sm"
                      value={partnerId}
                      disabled={!!todayRecord?.check_out_at}
                      onChange={(e) => setPartnerId(e.target.value)}
                    >
                      <option value="">No partner</option>
                      {partners.map((partner) => (
                        <option key={partner.id} value={partner.id}>
                          {partner.first_name} {partner.last_name}
                        </option>
                      ))}
                    </select>
                    {todayRecord?.partner_employee_name && (
                      <p className="text-xs text-muted-foreground">
                        Photos for this shift are split with {todayRecord.partner_employee_name}.
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Button disabled={submitting || !!todayRecord} onClick={handleCheckIn}>
                      Check In
                    </Button>
                    <Button
                      variant="outline"
                      disabled={submitting || !todayRecord || !!todayRecord.check_out_at}
                      onClick={handleCheckOut}
                    >
                      Check Out
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ) : (
          <>
            <Card>
              <CardContent className="grid gap-4 p-4 md:grid-cols-4">
                <div>
                  <Label>From</Label>
                  <Input
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>To</Label>
                  <Input
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Employee</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-white px-3 text-sm"
                    value={filters.employee_id}
                    onChange={(e) => setFilters({ ...filters, employee_id: e.target.value })}
                  >
                    <option value="">All employees</option>
                    {employees.map((employee) => (
                      <option key={employee.id} value={employee.id}>
                        {employee.first_name} {employee.last_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-end gap-2">
                  <Button variant="outline" className="gap-2" onClick={() => download("excel")}>
                    <Download className="h-4 w-4" />
                    Excel
                  </Button>
                  <Button variant="outline" onClick={() => download("csv")}>CSV</Button>
                  <Button variant="outline" onClick={() => download("pdf")}>PDF</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="overflow-x-auto p-0">
                {loading ? (
                  <div className="flex h-32 items-center justify-center">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </div>
                ) : records.length === 0 ? (
                  <p className="p-6 text-muted-foreground">No attendance records for this range.</p>
                ) : (
                  <table className="w-full min-w-[760px] text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="p-4 text-left">Employee</th>
                        <th className="p-4 text-left">Partner</th>
                        <th className="p-4 text-left">Branch</th>
                        <th className="p-4 text-left">Date</th>
                        <th className="p-4 text-left">Check In</th>
                        <th className="p-4 text-left">Check Out</th>
                        <th className="p-4 text-left">Total</th>
                        <th className="p-4 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((record) => (
                        <tr key={record.id} className="border-b">
                          <td className="p-4 font-medium">{record.employee_name || `Employee #${record.employee_id}`}</td>
                          <td className="p-4">{record.partner_employee_name || "-"}</td>
                          <td className="p-4">{record.branch_name || "-"}</td>
                          <td className="p-4">{formatDate(record.work_date)}</td>
                          <td className="p-4">{formatTime(record.check_in_at)}</td>
                          <td className="p-4">{formatTime(record.check_out_at)}</td>
                          <td className="p-4">{formatDuration(record.total_minutes)}</td>
                          <td className="p-4 capitalize">{record.status.replace("_", " ")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
