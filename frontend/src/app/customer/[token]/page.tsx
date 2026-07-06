"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency, formatDate, resolveAssetUrl } from "@/lib/utils";

export default function CustomerPortalPage({ params }: { params: Promise<{ token: string }> }) {
  const [token, setToken] = useState("");
  const [data, setData] = useState<{
    customer: { name: string };
    photos: { id: number; file_name: string; url?: string }[];
    sales: {
      id: number;
      amount: number;
      small_photo_count?: number;
      large_photo_count?: number;
      photo_count?: number;
      invoice_url?: string;
      created_at: string;
      notes?: string;
    }[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    params.then((p) => {
      setToken(p.token);
      api.getPortal(p.token)
        .then(setData)
        .catch(() => setError("Invalid or expired link"))
        .finally(() => setLoading(false));
    });
  }, [params]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-white border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">{error || "Not found"}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4 sm:p-6">
      <div className="mx-auto max-w-4xl space-y-8">
        <header className="text-center">
          <h1 className="text-2xl font-bold sm:text-3xl">Your Photo Gallery</h1>
          <p className="text-muted-foreground">Welcome, {data.customer.name}</p>
        </header>

        <section>
          <h2 className="mb-4 text-xl font-semibold">Photos</h2>
          {data.photos.length === 0 ? (
            <p className="text-muted-foreground">No photos yet</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
              {data.photos.map((photo) => (
                <div key={photo.id} className="group relative overflow-hidden rounded-lg border">
                  <img
                    src={resolveAssetUrl(photo.url)}
                    alt={photo.file_name}
                    className="aspect-square w-full object-cover"
                  />
                  <a
                    href={resolveAssetUrl(`/api/v1/portal/${token}/photos/${photo.id}/download`)}
                    className="absolute bottom-2 right-2 rounded-md bg-black/70 p-2 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100"
                  >
                    <Download className="h-4 w-4" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold">Order History</h2>
          {data.sales.length === 0 ? (
            <p className="text-muted-foreground">No orders yet</p>
          ) : (
            <div className="space-y-2">
              {data.sales.map((sale) => (
                <div key={sale.id} className="flex flex-col gap-2 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">Order #{sale.id}</p>
                    <p className="text-sm text-muted-foreground">
                      {sale.photo_count ? `${sale.photo_count} photos (${sale.small_photo_count || 0} small, ${sale.large_photo_count || 0} large) - ` : ""}{formatDate(sale.created_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{formatCurrency(sale.amount)}</span>
                    {sale.invoice_url && (
                      <a
                        href={sale.invoice_url}
                        className="inline-flex h-9 items-center rounded-md border border-input bg-background px-3 text-sm font-medium"
                      >
                        Invoice
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
