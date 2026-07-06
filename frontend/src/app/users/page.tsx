"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, User } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function UsersPage() {
  const { user } = useAuth();
  const isManager = user?.role === "manager";
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", role: "employee", password: "" });
  const [roleDrafts, setRoleDrafts] = useState<Record<number, string>>({});

  const load = () => {
    setLoading(true);
    api.getUsers(isManager ? { role: "employee", page_size: "100" } : { page_size: "100" })
      .then((r) => {
        setUsers(r.items);
        const drafts: Record<number, string> = {};
        r.items.forEach((u) => {
          drafts[u.id] = u.role;
        });
        setRoleDrafts(drafts);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [isManager]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createUser({
        ...form,
        role: isManager ? "employee" : form.role,
      });
      toast({ title: isManager ? "Employee created" : "User created" });
      setShowForm(false);
      setForm({ first_name: "", last_name: "", email: "", role: "employee", password: "" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleRoleSave = async (target: User) => {
    const role = roleDrafts[target.id];
    if (!role || role === target.role) return;
    try {
      await api.updateUser(target.id, { role });
      toast({ title: "Role updated" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this user?")) return;
    try {
      await api.deleteUser(id);
      toast({ title: "User deleted" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="mobile-page-header">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">{isManager ? "Employees" : "Users"}</h1>
            {isManager ? (
              <p className="text-muted-foreground">Add employees to your team.</p>
            ) : (
              <p className="text-muted-foreground">Create users and edit their roles only.</p>
            )}
          </div>
          <Button className="w-full sm:w-auto" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : isManager ? "Add Employee" : "Create User"}
          </Button>
        </div>

        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle>{isManager ? "New Employee" : "New User"}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>First Name</Label>
                  <Input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required />
                </div>
                <div>
                  <Label>Last Name</Label>
                  <Input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                </div>
                {!isManager && (
                  <div>
                    <Label>Role</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                    >
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="employee">Employee</option>
                    </select>
                  </div>
                )}
                <div className={isManager ? "" : "md:col-span-2"}>
                  <Label>Password</Label>
                  <Input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    minLength={8}
                  />
                </div>
                <div><Button type="submit" className="w-full sm:w-auto">{isManager ? "Add Employee" : "Create"}</Button></div>
              </form>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : users.length === 0 ? (
              <p className="p-6 text-muted-foreground">No users yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-4 text-left">Name</th>
                    <th className="p-4 text-left">Email</th>
                    {!isManager && <th className="p-4 text-left">Role</th>}
                    <th className="p-4 text-left">Status</th>
                    {!isManager && <th className="p-4 text-left">Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => {
                    const isSelf = user?.id === u.id;
                    const roleChanged = roleDrafts[u.id] !== u.role;
                    return (
                      <tr key={u.id} className="border-b">
                        <td className="p-4">{u.first_name} {u.last_name}</td>
                        <td className="p-4">{u.email}</td>
                        {!isManager && (
                          <td className="p-4">
                            <select
                              className="flex h-10 min-w-[140px] rounded-md border border-input bg-white px-3 text-sm capitalize disabled:opacity-50"
                              value={roleDrafts[u.id] ?? u.role}
                              disabled={isSelf}
                              onChange={(e) => setRoleDrafts({ ...roleDrafts, [u.id]: e.target.value })}
                            >
                              <option value="admin">Admin</option>
                              <option value="manager">Manager</option>
                              <option value="employee">Employee</option>
                            </select>
                            {isSelf && (
                              <p className="mt-1 text-xs text-muted-foreground">You cannot change your own role</p>
                            )}
                          </td>
                        )}
                        <td className="p-4">{u.is_active ? "Active" : "Inactive"}</td>
                        {!isManager && (
                          <td className="p-4">
                            <div className="flex flex-wrap gap-2">
                              <Button
                                size="sm"
                                disabled={!roleChanged || isSelf}
                                onClick={() => handleRoleSave(u)}
                              >
                                Save Role
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                disabled={isSelf}
                                onClick={() => handleDelete(u.id)}
                              >
                                Delete
                              </Button>
                            </div>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
