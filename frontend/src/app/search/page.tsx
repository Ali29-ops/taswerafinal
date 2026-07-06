"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ type: string; id: number; title: string; subtitle?: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (q: string) => {
    setQuery(q);
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const r = await api.search(q);
      setResults(r);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold sm:text-3xl">Search</h1>
        <Input
          placeholder="Search customers, employees, managers, sales..."
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          className="max-w-xl"
        />
        {loading && <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />}
        <div className="space-y-2">
          {results.map((r) => (
            <Card key={`${r.type}-${r.id}`}>
              <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="font-medium">{r.title}</p>
                  {r.subtitle && <p className="text-sm text-muted-foreground">{r.subtitle}</p>}
                </div>
                <span className="w-fit rounded-full bg-secondary px-3 py-1 text-xs capitalize">{r.type}</span>
              </CardContent>
            </Card>
          ))}
          {query.length >= 2 && !loading && results.length === 0 && (
            <p className="text-muted-foreground">No results found</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
