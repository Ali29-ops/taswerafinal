"use client";

import { useEffect, useState } from "react";
import { QrCode } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Customer } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [qrImage, setQrImage] = useState<string | null>(null);

  const load = () => {
    const params: Record<string, string> = {};
    if (search) params.search = search;
    api.getCustomers(params).then((r) => setCustomers(r.items)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCustomer(form);
      toast({ title: "Customer created" });
      setShowForm(false);
      setForm({ name: "", email: "", phone: "" });
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const showQR = async (id: number) => {
    try {
      const qr = await api.getCustomerQR(id);
      setQrImage(qr.qr_image_base64);
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="mobile-page-header">
          <h1 className="text-2xl font-bold sm:text-3xl">Customers</h1>
          <div className="mobile-action-row">
            <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full sm:w-48" />
            <Button className="w-full sm:w-auto" onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add Customer"}</Button>
          </div>
        </div>

        {showForm && (
          <Card>
            <CardHeader><CardTitle>New Customer</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-3">
                <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
                <div><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
                <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
                <div><Button type="submit" className="w-full sm:w-auto">Create</Button></div>
              </form>
            </CardContent>
          </Card>
        )}

        {qrImage && (
          <Card>
            <CardContent className="flex flex-col items-center gap-4 p-6">
              <img src={qrImage} alt="QR Code" className="h-48 w-48" />
              <Button variant="outline" onClick={() => setQrImage(null)}>Close</Button>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex h-32 items-center justify-center"><div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>
            ) : (
              <table className="w-full text-sm">
                <thead><tr className="border-b"><th className="p-4 text-left">Name</th><th className="p-4 text-left">Email</th><th className="p-4 text-left">Phone</th><th className="p-4"></th></tr></thead>
                <tbody>
                  {customers.map((c) => (
                    <tr key={c.id} className="border-b">
                      <td className="p-4">{c.name}</td>
                      <td className="p-4">{c.email || "-"}</td>
                      <td className="p-4">{c.phone || "-"}</td>
                      <td className="p-4">
                        <Button variant="outline" size="sm" onClick={() => showQR(c.id)}>
                          <QrCode className="mr-1 h-4 w-4" /> QR
                        </Button>
                      </td>
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
