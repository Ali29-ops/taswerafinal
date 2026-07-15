"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { api, PrintPackage } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

const emptyForm = {
  name: "",
  photo_count: "10",
  price: "1000",
};

export default function PackagesPage() {
  const [packages, setPackages] = useState<PrintPackage[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.getPackages(true).then(setPackages).finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const createPackage = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPackage({
        name: form.name,
        photo_count: Number(form.photo_count),
        price: Number(form.price),
        is_active: true,
      });
      toast({ title: "Package created" });
      setForm(emptyForm);
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const togglePackage = async (pkg: PrintPackage) => {
    try {
      await api.updatePackage(pkg.id, { is_active: !pkg.is_active });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const deletePackage = async (id: number) => {
    try {
      await api.deletePackage(id);
      toast({ title: "Package deleted" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Packages</h1>
          <p className="text-muted-foreground">Create custom package prices for print orders</p>
        </div>

        <Card>
          <CardHeader><CardTitle>New Package</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={createPackage} className="grid gap-4 md:grid-cols-4">
              <div className="md:col-span-2">
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="10 photo package"
                  required
                />
              </div>
              <div>
                <Label>Photos</Label>
                <Input
                  type="number"
                  min="1"
                  step="1"
                  value={form.photo_count}
                  onChange={(e) => setForm({ ...form, photo_count: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>Package Price</Label>
                <Input
                  type="number"
                  min="1"
                  step="0.01"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  required
                />
              </div>
              <div className="md:col-span-4">
                <Button type="submit" className="w-full sm:w-auto">Create Package</Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="overflow-x-auto p-0">
            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : (
              <table className="w-full min-w-[700px] text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-4 text-left">Name</th>
                    <th className="p-4 text-left">Photos</th>
                    <th className="p-4 text-left">Price</th>
                    <th className="p-4 text-left">Per Photo</th>
                    <th className="p-4 text-left">Status</th>
                    <th className="p-4 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {packages.map((pkg) => (
                    <tr key={pkg.id} className="border-b">
                      <td className="p-4 font-medium">{pkg.name}</td>
                      <td className="p-4">{pkg.photo_count}</td>
                      <td className="p-4 font-semibold">{formatCurrency(pkg.price)}</td>
                      <td className="p-4">{formatCurrency(pkg.price / pkg.photo_count)}</td>
                      <td className="p-4">{pkg.is_active ? "Active" : "Inactive"}</td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => togglePackage(pkg)}>
                            {pkg.is_active ? "Disable" : "Enable"}
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => deletePackage(pkg.id)}>Delete</Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {packages.length === 0 && (
                    <tr>
                      <td className="p-6 text-center text-muted-foreground" colSpan={6}>No packages yet</td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
