"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

export default function SettingsPage() {
  const [price, setPrice] = useState("120");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getPrintPrice()
      .then((r) => setPrice(String(r.price_per_photo)))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await api.updatePrintPrice(Number(price));
      setPrice(String(updated.price_per_photo));
      toast({ title: "Print price updated", description: `New price: ${formatCurrency(updated.price_per_photo)} per photo` });
    } catch (err) {
      toast({ title: "Error", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold sm:text-3xl">Print Pricing</h1>
          <p className="text-muted-foreground">Set the price employees charge per printed photo</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Price Per Photo</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-20 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              </div>
            ) : (
              <form onSubmit={handleSave} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="price">Price (EGP)</Label>
                  <Input
                    id="price"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Employees enter how many photos were printed. Total = photos × this price.
                  </p>
                </div>
                <Button type="submit" disabled={saving} className="w-full sm:w-auto">
                  {saving ? "Saving..." : "Save Price"}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
