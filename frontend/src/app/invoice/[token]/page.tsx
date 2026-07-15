"use client";

import { useEffect, useMemo } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export default function InvoicePage({ params }: { params: Promise<{ token: string }> }) {
  const downloadUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    const parts = window.location.pathname.split("/");
    const token = parts[parts.length - 1];
    return `${API_URL}/portal/invoices/${token}/download`;
  }, []);

  useEffect(() => {
    params.then((p) => {
      window.location.href = `${API_URL}/portal/invoices/${p.token}/download`;
    });
  }, [params]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-secondary/40 p-6">
      <div className="w-full max-w-md rounded-md border bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold">TASWERA Invoice</h1>
        <p className="mt-2 text-sm text-muted-foreground">Your invoice download should start automatically.</p>
        {downloadUrl && (
          <Button asChild className="mt-6">
            <a href={downloadUrl}>
              <Download className="h-4 w-4" />
              Download Invoice
            </a>
          </Button>
        )}
      </div>
    </main>
  );
}
