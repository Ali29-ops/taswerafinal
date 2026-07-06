"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) {
      if (user.role === "employee") {
        router.push(user.current_branch_id ? "/attendance" : "/select-branch");
      } else if (user.role === "manager") {
        router.push(user.current_branch_id ? "/dashboard" : "/select-branch");
      } else {
        router.push("/dashboard");
      }
    }
  }, [loading, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const loggedIn = await login(email, password);
      toast({ title: "Welcome back!" });
      if (loggedIn.role === "employee" || loggedIn.role === "manager") {
        router.push("/select-branch");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      toast({
        title: "Login failed",
        description: err instanceof Error ? err.message : "Invalid credentials",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (!loading && user) {
    return null;
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden flex-1 flex-col justify-between bg-white p-12 lg:flex">
        <Logo height={40} />
        <div className="max-w-md space-y-4">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">TASWERA</h1>
          <p className="text-lg text-muted-foreground">Sign in to your account.</p>
        </div>
        <p className="text-sm text-muted-foreground">© CODAI_EG</p>
      </div>

      <div className="flex flex-1 items-center justify-center bg-secondary/40 p-6">
        <Card className="w-full max-w-md border-border shadow-lg">
          <CardContent className="space-y-6 p-8">
            <div className="flex flex-col items-center gap-3 text-center lg:hidden">
              <Logo height={36} />
            </div>
            <div className="space-y-1 text-center">
              <h2 className="text-xl font-semibold">Sign in</h2>
              <p className="text-sm text-muted-foreground">Enter your account credentials</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-white"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-white"
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Signing in..." : "Sign In"}
              </Button>
              <div className="text-center text-sm">
                <Link href="/forgot-password" className="text-muted-foreground hover:text-foreground">
                  Forgot password?
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
