"use client";

import { useEffect, useMemo, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { api, User } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

type Assignment = {
  id: number;
  manager_id: number;
  employee_id: number;
  manager_name?: string;
  employee_name?: string;
};

type Draft = {
  manager_id: string;
  employee_id: string;
};

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [managers, setManagers] = useState<User[]>([]);
  const [employees, setEmployees] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [managerId, setManagerId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getAssignments(),
      api.getUsers({ role: "manager", page_size: "100" }),
      api.getUsers({ role: "employee", page_size: "100" }),
    ])
      .then(([a, m, e]) => {
        setAssignments(a);
        setManagers(m.items);
        setEmployees(e.items);
        const nextDrafts: Record<number, Draft> = {};
        a.forEach((item) => {
          nextDrafts[item.id] = {
            manager_id: String(item.manager_id),
            employee_id: String(item.employee_id),
          };
        });
        setDrafts(nextDrafts);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const groupedByManager = useMemo(() => {
    const groups = new Map<number, { manager: User | undefined; items: Assignment[] }>();
    managers.forEach((manager) => {
      groups.set(manager.id, { manager, items: [] });
    });
    assignments.forEach((assignment) => {
      const group = groups.get(assignment.manager_id) ?? {
        manager: managers.find((m) => m.id === assignment.manager_id),
        items: [],
      };
      group.items.push(assignment);
      groups.set(assignment.manager_id, group);
    });
    return Array.from(groups.entries())
      .map(([id, group]) => ({ id, ...group }))
      .sort((a, b) => {
        const nameA = a.manager ? `${a.manager.first_name} ${a.manager.last_name}` : "";
        const nameB = b.manager ? `${b.manager.first_name} ${b.manager.last_name}` : "";
        return nameA.localeCompare(nameB);
      });
  }, [assignments, managers]);

  const handleAssign = async () => {
    if (!managerId || !employeeId) return;
    try {
      await api.createAssignment(Number(managerId), Number(employeeId));
      toast({ title: "Assignment created" });
      setManagerId("");
      setEmployeeId("");
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleSave = async (assignment: Assignment) => {
    const draft = drafts[assignment.id];
    if (!draft?.manager_id || !draft?.employee_id) return;
    try {
      await api.updateAssignment(assignment.id, {
        manager_id: Number(draft.manager_id),
        employee_id: Number(draft.employee_id),
      });
      toast({ title: "Assignment updated" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Remove this assignment?")) return;
    try {
      await api.deleteAssignment(id);
      toast({ title: "Assignment removed" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const updateDraft = (id: number, field: keyof Draft, value: string) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        manager_id: prev[id]?.manager_id ?? "",
        employee_id: prev[id]?.employee_id ?? "",
        [field]: value,
      },
    }));
  };

  const isDirty = (assignment: Assignment) => {
    const draft = drafts[assignment.id];
    if (!draft) return false;
    return (
      draft.manager_id !== String(assignment.manager_id) ||
      draft.employee_id !== String(assignment.employee_id)
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Manager Assignments</h1>
          <p className="text-muted-foreground">
            Assign employees to managers, edit assignments, or remove them.
          </p>
        </div>

        <Card>
          <CardHeader><CardTitle>Add Assignment</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:flex sm:flex-wrap sm:items-end">
            <div className="w-full sm:w-auto">
              <Label>Manager</Label>
              <select
                className="mt-1 flex h-10 w-full rounded-md border border-input bg-white px-3 text-sm sm:min-w-[200px]"
                value={managerId}
                onChange={(e) => setManagerId(e.target.value)}
              >
                <option value="">Select Manager</option>
                {managers.map((m) => (
                  <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
                ))}
              </select>
            </div>
            <div className="w-full sm:w-auto">
              <Label>Employee</Label>
              <select
                className="mt-1 flex h-10 w-full rounded-md border border-input bg-white px-3 text-sm sm:min-w-[200px]"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
              >
                <option value="">Select Employee</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                ))}
              </select>
            </div>
            <Button onClick={handleAssign} className="w-full sm:w-auto">Assign</Button>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
          </div>
        ) : (
          groupedByManager.map(({ id, manager, items }) => (
            <Card key={id}>
              <CardHeader>
                <CardTitle>
                  {manager ? `${manager.first_name} ${manager.last_name}` : `Manager #${id}`}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {items.length === 0 ? (
                  <p className="p-4 text-sm text-muted-foreground">No employees assigned yet.</p>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="p-4 text-left">Manager</th>
                        <th className="p-4 text-left">Employee</th>
                        <th className="p-4 text-left">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((assignment) => (
                        <tr key={assignment.id} className="border-b">
                          <td className="p-4">
                            <select
                              className="flex h-10 min-w-[180px] rounded-md border border-input bg-white px-3 text-sm"
                              value={drafts[assignment.id]?.manager_id ?? String(assignment.manager_id)}
                              onChange={(e) => updateDraft(assignment.id, "manager_id", e.target.value)}
                            >
                              {managers.map((m) => (
                                <option key={m.id} value={m.id}>{m.first_name} {m.last_name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-4">
                            <select
                              className="flex h-10 min-w-[180px] rounded-md border border-input bg-white px-3 text-sm"
                              value={drafts[assignment.id]?.employee_id ?? String(assignment.employee_id)}
                              onChange={(e) => updateDraft(assignment.id, "employee_id", e.target.value)}
                            >
                              {employees.map((e) => (
                                <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-4">
                            <div className="flex flex-wrap gap-2">
                              <Button
                                size="sm"
                                disabled={!isDirty(assignment)}
                                onClick={() => handleSave(assignment)}
                              >
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDelete(assignment.id)}
                              >
                                Remove
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </DashboardLayout>
  );
}
