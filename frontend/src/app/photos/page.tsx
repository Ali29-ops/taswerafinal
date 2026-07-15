"use client";

import { useCallback, useEffect, useState } from "react";
import { Upload } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Customer, Photo } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { cn, resolveAssetUrl } from "@/lib/utils";

export default function PhotosPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [previews, setPreviews] = useState<string[]>([]);

  useEffect(() => {
    api.getCustomers().then((r) => {
      setCustomers(r.items);
      if (r.items.length) setCustomerId(r.items[0].id);
    });
  }, []);

  useEffect(() => {
    if (customerId) api.getPhotos({ customer_id: String(customerId) }).then((r) => setPhotos(r.items));
  }, [customerId]);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    if (!customerId) {
      toast({ title: "Select a customer first", variant: "destructive" });
      return;
    }
    const valid = Array.from(files).filter((f) => ["image/jpeg", "image/png", "image/webp"].includes(f.type));
    const tooLarge = valid.find((f) => f.size > 50 * 1024 * 1024);
    if (!valid.length) {
      toast({ title: "Invalid files", description: "Only JPG, PNG, WEBP allowed", variant: "destructive" });
      return;
    }
    if (tooLarge) {
      toast({ title: "File too large", description: "Each photo must be 50MB or less", variant: "destructive" });
      return;
    }
    setPreviews(valid.map((f) => URL.createObjectURL(f)));
    setUploading(true);
    try {
      await api.uploadPhotos(customerId, valid, setProgress);
      toast({ title: "Upload complete" });
      const r = await api.getPhotos({ customer_id: String(customerId) });
      setPhotos(r.items);
    } catch (err) {
      toast({ title: "Upload failed", description: err instanceof Error ? err.message : "Failed", variant: "destructive" });
    } finally {
      setUploading(false);
      setProgress(0);
      setPreviews([]);
    }
  }, [customerId]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold sm:text-3xl">Photos</h1>

        <div className="grid gap-4 sm:flex">
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm sm:w-auto"
            value={customerId || ""}
            onChange={(e) => setCustomerId(Number(e.target.value))}
          >
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <Card>
          <CardHeader><CardTitle>Upload Photos</CardTitle></CardHeader>
          <CardContent>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              className={cn(
                "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition-colors sm:p-12",
                dragging ? "border-primary bg-accent/50" : "border-border"
              )}
            >
              <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
              <p className="mb-2 text-sm text-muted-foreground">Drag and drop images here, or click to browse</p>
              <p className="mb-4 text-xs text-muted-foreground">JPG, PNG, WEBP - max 50MB per file, original quality kept, bulk uploads are batched</p>
              <input
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                id="file-upload"
                onChange={(e) => e.target.files && handleFiles(e.target.files)}
              />
              <Button variant="outline" asChild disabled={uploading} className="w-full sm:w-auto">
                <label htmlFor="file-upload" className="cursor-pointer">Browse Files</label>
              </Button>
              {uploading && (
                <div className="mt-4 w-full max-w-xs">
                  <div className="h-2 overflow-hidden rounded-full bg-secondary">
                    <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
                  </div>
                  <p className="mt-1 text-center text-xs text-muted-foreground">{progress}%</p>
                </div>
              )}
            </div>

            {previews.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {previews.map((p, i) => (
                  <img key={i} src={p} alt="Preview" className="h-20 w-20 rounded object-cover" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {photos.map((photo) => (
            <Card key={photo.id} className="overflow-hidden">
              <img
                src={resolveAssetUrl(photo.url)}
                alt={photo.file_name}
                className="aspect-square w-full object-cover"
              />
              <CardContent className="p-3">
                <p className="truncate text-xs text-muted-foreground">{photo.file_name}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
