"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Branch, Customer, Sale, SaleInvoiceQR } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

const emptyForm = {
  customer_id: "",
  branch_id: "",
  small_photo_count: "0",
  large_photo_count: "0",
  notes: "",
};

export default function SalesPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [sales, setSales] = useState<Sale[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [printPrice, setPrintPrice] = useState(120);
  const [branchLabel, setBranchLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [invoiceQR, setInvoiceQR] = useState<SaleInvoiceQR | null>(null);

  const selectedBranchPrice = isAdmin && form.branch_id
    ? branches.find((b) => b.id === Number(form.branch_id))?.price_per_photo ?? printPrice
    : printPrice;
  const totalPhotos = Number(form.small_photo_count || 0) + Number(form.large_photo_count || 0);
  const totalPreview = totalPhotos * selectedBranchPrice;

  const load = () => {
    Promise.all([api.getSales(), api.getPrintPrice()])
      .then(([salesRes, priceRes]) => {
        setSales(salesRes.items);
        setPrintPrice(priceRes.price_per_photo);
        setBranchLabel(priceRes.branch_name ?? user?.current_branch_name ?? null);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    api.getCustomers().then((r) => setCustomers(r.items));
    if (isAdmin) {
      api.getBranches().then(setBranches);
    }
  }, [isAdmin, user?.current_branch_name]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (totalPhotos <= 0) {
      toast({ title: "Add photos", description: "Enter at least one small or large image.", variant: "destructive" });
      return;
    }
    try {
      const sale = await api.createSale({
        customer_id: Number(form.customer_id),
        small_photo_count: Number(form.small_photo_count),
        large_photo_count: Number(form.large_photo_count),
        notes: form.notes || undefined,
        ...(isAdmin && form.branch_id ? { branch_id: Number(form.branch_id) } : {}),
      });
      toast({ title: "Print order recorded" });
      setInvoiceQR(await api.getSaleInvoiceQR(sale.id));
      setShowForm(false);
      setForm(emptyForm);
      load();
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  const showInvoiceQR = async (saleId: number) => {
    try {
      setInvoiceQR(await api.getSaleInvoiceQR(saleId));
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="mobile-page-header">
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">Print Sales</h1>
            <p className="text-sm text-muted-foreground">
              {branchLabel ? `${branchLabel} - ` : ""}
              {formatCurrency(printPrice)} per photo
            </p>
          </div>
          <Button className="w-full sm:w-auto" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "New Print Order"}
          </Button>
        </div>

        {showForm && (
          <Card>
            <CardHeader><CardTitle>Record Printed Photos</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
                {isAdmin && (
                  <div>
                    <Label>Branch</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                      value={form.branch_id}
                      onChange={(e) => setForm({ ...form, branch_id: e.target.value })}
                      required
                    >
                      <option value="">Select branch</option>
                      {branches.filter((b) => b.is_active).map((b) => (
                        <option key={b.id} value={b.id}>{b.name} - {formatCurrency(b.price_per_photo)}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <Label>Customer</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={form.customer_id}
                    onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                    required
                  >
                    <option value="">Select customer</option>
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Small Images</Label>
                  <Input
                    type="number"
                    min="0"
                    step="1"
                    value={form.small_photo_count}
                    onChange={(e) => setForm({ ...form, small_photo_count: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Large Images</Label>
                  <Input
                    type="number"
                    min="0"
                    step="1"
                    value={form.large_photo_count}
                    onChange={(e) => setForm({ ...form, large_photo_count: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>Notes (optional)</Label>
                  <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                </div>
                <div className="flex items-end">
                  <div className="w-full rounded-lg border bg-secondary/30 p-4">
                    <p className="text-sm text-muted-foreground">Total amount</p>
                    <p className="text-2xl font-bold">{formatCurrency(totalPreview)}</p>
                    <p className="text-xs text-muted-foreground">
                      {totalPhotos} photos ({form.small_photo_count || 0} small, {form.large_photo_count || 0} large) x {formatCurrency(selectedBranchPrice)}
                    </p>
                  </div>
                </div>
                <div className="md:col-span-2">
                  <Button type="submit" className="w-full sm:w-auto">Save Print Order</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {invoiceQR && (
          <Card>
            <CardHeader><CardTitle>Invoice QR</CardTitle></CardHeader>
            <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <img src={invoiceQR.qr_image_base64} alt="Invoice QR" className="h-40 w-40 rounded-md border bg-white p-2" />
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Scan this QR to open and download the customer invoice.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button asChild>
                    <a href={invoiceQR.invoice_url} target="_blank" rel="noreferrer">Open Invoice</a>
                  </Button>
                  <Button variant="outline" onClick={() => setInvoiceQR(null)}>Close</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="overflow-x-auto p-0">
            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : (
              <table className="w-full min-w-[900px] text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-4 text-left">ID</th>
                    <th className="p-4 text-left">Branch</th>
                    <th className="p-4 text-left">Customer</th>
                    <th className="p-4 text-left">Employee</th>
                    <th className="p-4 text-left">Small</th>
                    <th className="p-4 text-left">Large</th>
                    <th className="p-4 text-left">Total Photos</th>
                    <th className="p-4 text-left">Price/Photo</th>
                    <th className="p-4 text-left">Total</th>
                    <th className="p-4 text-left">Date</th>
                    <th className="p-4 text-left">Invoice</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map((s) => (
                    <tr key={s.id} className="border-b">
                      <td className="p-4">#{s.id}</td>
                      <td className="p-4">{s.branch_name || "-"}</td>
                      <td className="p-4">{s.customer_name || s.customer_id}</td>
                      <td className="p-4">{s.employee_name || s.employee_id}</td>
                      <td className="p-4">{s.small_photo_count}</td>
                      <td className="p-4">{s.large_photo_count}</td>
                      <td className="p-4 font-medium">{s.photo_count}</td>
                      <td className="p-4">{formatCurrency(s.price_per_photo)}</td>
                      <td className="p-4 font-semibold">{formatCurrency(s.amount)}</td>
                      <td className="p-4">{formatDate(s.created_at)}</td>
                      <td className="p-4">
                        <Button variant="outline" size="sm" onClick={() => showInvoiceQR(s.id)}>QR</Button>
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
