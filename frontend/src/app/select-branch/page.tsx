"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/logo";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { api, Branch } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

export default function SelectBranchPage() {
  const { user, loading, selectBranch, logout } = useAuth();
  const router = useRouter();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchId, setBranchId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loadingBranches, setLoadingBranches] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role !== "employee" && user.role !== "manager") {
      router.push("/dashboard");
      return;
    }
    api.getMyBranches()
      .then(setBranches)
      .catch(() => toast({ title: "Failed to load branches", variant: "destructive" }))
      .finally(() => setLoadingBranches(false));
  }, [user, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!branchId) return;
    setSubmitting(true);
    try {
      await selectBranch(Number(branchId));
      toast({ title: "Branch selected" });
      router.push(user?.role === "employee" ? "/attendance" : "/dashboard");
    } catch (err) {
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to select branch",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || loadingBranches || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-secondary/40 p-6">
      <Card className="w-full max-w-md border-border shadow-lg">
        <CardContent className="space-y-6 p-8">
          <div className="flex flex-col items-center gap-3 text-center">
            <Logo height={36} />
            <h2 className="text-xl font-semibold">Select your branch</h2>
            <p className="text-sm text-muted-foreground">
              Hi {user.first_name}, choose which branch you are working at today.
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="branch">Branch today</Label>
              <select
                id="branch"
                className="flex h-10 w-full rounded-md border border-input bg-white px-3 text-sm"
                value={branchId}
                onChange={(e) => setBranchId(e.target.value)}
                required
              >
                <option value="">Select branch</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} — {formatCurrency(b.price_per_photo)}/photo
                  </option>
                ))}
              </select>
            </div>
            <Button type="submit" className="w-full" disabled={submitting || branches.length === 0}>
              {submitting ? "Continuing..." : "Continue"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() => logout().then(() => router.push("/login"))}
            >
              Sign out
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
