"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Branch, User } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

type BranchDraft = {
  name: string;
  price_per_photo: string;
  commission_per_photo: string;
  commission_after_target_per_photo: string;
  is_active: boolean;
};

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [employees, setEmployees] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<number | null>(null);
  const [assignedIds, setAssignedIds] = useState<number[]>([]);
  const [form, setForm] = useState({
    name: "",
    code: "",
    price_per_photo: "120",
    commission_per_photo: "6",
    commission_after_target_per_photo: "12",
  });
  const [editDrafts, setEditDrafts] = useState<Record<number, BranchDraft>>({});

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getBranches(),
      api.getUsers({ role: "employee", page_size: "100" }),
    ])
      .then(([b, e]) => {
        setBranches(b);
        setEmployees(e.items);
        const drafts: Record<number, BranchDraft> = {};
        b.forEach((branch) => {
          drafts[branch.id] = {
            name: branch.name,
            price_per_photo: String(branch.price_per_photo),
            commission_per_photo: String(branch.commission_per_photo),
            commission_after_target_per_photo: String(branch.commission_after_target_per_photo),
            is_active: branch.is_active,
          };
        });
        setEditDrafts(drafts);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const updateDraft = (branch: Branch, values: Partial<BranchDraft>) => {
    const current = editDrafts[branch.id] ?? {
      name: branch.name,
      price_per_photo: String(branch.price_per_photo),
      commission_per_photo: String(branch.commission_per_photo),
      commission_after_target_per_photo: String(branch.commission_after_target_per_photo),
      is_active: branch.is_active,
    };
    setEditDrafts({ ...editDrafts, [branch.id]: { ...current, ...values } });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createBranch({
        name: form.name,
        code: form.code || undefined,
        price_per_photo: Number(form.price_per_photo),
        commission_per_photo: Number(form.commission_per_photo),
        commission_after_target_per_photo: Number(form.commission_after_target_per_photo),
      });
      toast({ title: "Branch created" });
      setShowForm(false);
      setForm({
        name: "",
        code: "",
        price_per_photo: "120",
        commission_per_photo: "6",
        commission_after_target_per_photo: "12",
      });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleSaveBranch = async (branch: Branch) => {
    const draft = editDrafts[branch.id];
    if (!draft) return;
    try {
      await api.updateBranch(branch.id, {
        name: draft.name,
        price_per_photo: Number(draft.price_per_photo),
        commission_per_photo: Number(draft.commission_per_photo),
        commission_after_target_per_photo: Number(draft.commission_after_target_per_photo),
        is_active: draft.is_active,
      });
      toast({ title: "Branch updated" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this branch?")) return;
    try {
      await api.deleteBranch(id);
      toast({ title: "Branch deleted" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const openEmployees = async (branchId: number) => {
    setSelectedBranch(branchId);
    const ids = await api.getBranchEmployees(branchId);
    setAssignedIds(ids);
  };

  const toggleEmployee = (id: number) => {
    setAssignedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const saveEmployees = async () => {
    if (!selectedBranch) return;
    try {
      await api.setBranchEmployees(selectedBranch, assignedIds);
      toast({ title: "Branch employees updated" });
      setSelectedBranch(null);
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="mobile-page-header">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">Branches</h1>
            <p className="text-muted-foreground">Manage branch pricing and commission rates per photo.</p>
          </div>
          <Button className="w-full sm:w-auto" onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add Branch"}</Button>
        </div>

        {showForm && (
          <Card>
            <CardHeader><CardTitle>New Branch</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                <div>
                  <Label>Branch Name</Label>
                  <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div>
                  <Label>Code (optional)</Label>
                  <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
                </div>
                <div>
                  <Label>Price per Photo (EGP)</Label>
                  <Input type="number" min="0.01" step="0.01" value={form.price_per_photo} onChange={(e) => setForm({ ...form, price_per_photo: e.target.value })} required />
                </div>
                <div>
                  <Label>Commission (EGP)</Label>
                  <Input type="number" min="0.01" step="0.01" value={form.commission_per_photo} onChange={(e) => setForm({ ...form, commission_per_photo: e.target.value })} required />
                </div>
                <div>
                  <Label>After Target (EGP)</Label>
                  <Input type="number" min="0.01" step="0.01" value={form.commission_after_target_per_photo} onChange={(e) => setForm({ ...form, commission_after_target_per_photo: e.target.value })} required />
                </div>
                <div><Button type="submit">Create Branch</Button></div>
              </form>
            </CardContent>
          </Card>
        )}

        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
          </div>
        ) : (
          <div className="grid gap-4">
            {branches.map((branch) => {
              const draft = editDrafts[branch.id];
              return (
                <Card key={branch.id}>
                  <CardContent className="flex flex-wrap items-end gap-4 p-6">
                    <div className="w-full min-w-[180px] flex-1">
                      <Label>Name</Label>
                      <Input
                        value={draft?.name ?? branch.name}
                        onChange={(e) => updateDraft(branch, { name: e.target.value })}
                      />
                    </div>
                    <div className="w-full sm:w-40">
                      <Label>Price (EGP)</Label>
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={draft?.price_per_photo ?? String(branch.price_per_photo)}
                        onChange={(e) => updateDraft(branch, { price_per_photo: e.target.value })}
                      />
                    </div>
                    <div className="w-full sm:w-44">
                      <Label>Commission (EGP)</Label>
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={draft?.commission_per_photo ?? String(branch.commission_per_photo)}
                        onChange={(e) => updateDraft(branch, { commission_per_photo: e.target.value })}
                      />
                    </div>
                    <div className="w-full sm:w-44">
                      <Label>After Target (EGP)</Label>
                      <Input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={draft?.commission_after_target_per_photo ?? String(branch.commission_after_target_per_photo)}
                        onChange={(e) => updateDraft(branch, { commission_after_target_per_photo: e.target.value })}
                      />
                    </div>
                    <div className="flex items-center gap-2 pb-2">
                      <input
                        type="checkbox"
                        id={`active-${branch.id}`}
                        checked={draft?.is_active ?? branch.is_active}
                        onChange={(e) => updateDraft(branch, { is_active: e.target.checked })}
                      />
                      <Label htmlFor={`active-${branch.id}`}>Active</Label>
                    </div>
                    <div className="grid w-full grid-cols-3 gap-2 sm:flex sm:w-auto sm:flex-wrap">
                      <Button size="sm" onClick={() => handleSaveBranch(branch)}>Save</Button>
                      <Button size="sm" variant="outline" onClick={() => openEmployees(branch.id)}>Employees</Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDelete(branch.id)}>Delete</Button>
                    </div>
                    <p className="w-full text-sm text-muted-foreground">
                      Current price: <strong>{formatCurrency(branch.price_per_photo)}</strong> per photo.
                      Commission: <strong>{formatCurrency(branch.commission_per_photo)}</strong> before target,
                      <strong> {formatCurrency(branch.commission_after_target_per_photo)}</strong> after target.
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {selectedBranch !== null && (
          <Card>
            <CardHeader>
              <CardTitle>Assign Employees — {branches.find((b) => b.id === selectedBranch)?.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2 md:grid-cols-2">
                {employees.map((emp) => (
                  <label key={emp.id} className="flex items-center gap-2 rounded-md border p-3">
                    <input
                      type="checkbox"
                      checked={assignedIds.includes(emp.id)}
                      onChange={() => toggleEmployee(emp.id)}
                    />
                    <span>{emp.first_name} {emp.last_name}</span>
                  </label>
                ))}
              </div>
              <div className="flex gap-2">
                <Button onClick={saveEmployees}>Save Assignments</Button>
                <Button variant="outline" onClick={() => setSelectedBranch(null)}>Cancel</Button>
              </div>
              <p className="text-xs text-muted-foreground">
                If no employees are assigned, all employees can select this branch at sign-in.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
