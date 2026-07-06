"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Camera,
  Clock,
  DollarSign,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
  Target,
  UserCircle,
  Users,
  Network,
  Building2,
  Menu,
  X,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "manager", "employee"] },
  { href: "/users", label: "Users", icon: Users, roles: ["admin", "manager"] },
  { href: "/customers", label: "Customers", icon: UserCircle, roles: ["admin", "manager", "employee"] },
  { href: "/photos", label: "Photos", icon: Camera, roles: ["admin", "manager", "employee"] },
  { href: "/sales", label: "Print Sales", icon: DollarSign, roles: ["admin", "manager", "employee"] },
  { href: "/attendance", label: "Attendance", icon: Clock, roles: ["admin", "manager", "employee"] },
  { href: "/branches", label: "Branches", icon: Building2, roles: ["admin"] },
  { href: "/settings", label: "Print Pricing", icon: Settings, roles: ["manager"] },
  { href: "/targets", label: "Employee Targets", icon: Target, roles: ["admin", "manager"] },
  { href: "/hierarchy", label: "Team Hierarchy", icon: Network, roles: ["admin", "manager"] },
  { href: "/reports", label: "Reports", icon: FileText, roles: ["admin", "manager"] },
  { href: "/assignments", label: "Assignments", icon: BarChart3, roles: ["admin"] },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-foreground border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    router.push("/login");
    return null;
  }

  const needsBranch = (user.role === "employee" || user.role === "manager") && !user.current_branch_id;
  if (needsBranch && pathname !== "/select-branch") {
    router.push("/select-branch");
    return null;
  }

  const filteredNav = navItems.filter((item) => item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 flex-col border-r border-border bg-white md:flex">
        <div className="flex h-20 items-center border-b border-border px-6">
          <Logo href="/dashboard" height={32} />
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {filteredNav.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            const label =
              item.href === "/users" && user.role === "manager" ? "Employees" : item.label;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-foreground text-background"
                    : "text-foreground/70 hover:bg-accent hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border p-4">
          <div className="mb-3 rounded-md bg-secondary px-3 py-2 text-sm">
            <p className="font-medium">{user.first_name} {user.last_name}</p>
            <p className="text-muted-foreground capitalize">{user.role}</p>
            {user.current_branch_name && (
              <p className="mt-1 text-xs text-muted-foreground">Branch: {user.current_branch_name}</p>
            )}
          </div>
          {(user.role === "employee" || user.role === "manager") && (
            <Button
              variant="ghost"
              className="mb-3 w-full justify-start text-sm"
              onClick={() => router.push("/select-branch")}
            >
              Change branch
            </Button>
          )}
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={() => logout().then(() => router.push("/login"))}
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-white px-4 md:hidden">
          <Logo href="/dashboard" height={28} />
          <Button
            variant="ghost"
            size="icon"
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
            onClick={() => setMobileOpen((open) => !open)}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </header>
        {mobileOpen && (
          <div className="border-b border-border bg-white p-3 md:hidden">
            <nav className="grid grid-cols-2 gap-2">
              {filteredNav.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                const label =
                  item.href === "/users" && user.role === "manager" ? "Employees" : item.label;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex min-h-11 items-center gap-2 rounded-md px-3 text-sm font-medium",
                      active
                        ? "bg-foreground text-background"
                        : "bg-secondary text-foreground/80"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate">{label}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="mt-3 rounded-md bg-secondary p-3 text-sm">
              <p className="font-medium">{user.first_name} {user.last_name}</p>
              <p className="text-muted-foreground capitalize">{user.role}</p>
              {user.current_branch_name && (
                <p className="mt-1 text-xs text-muted-foreground">Branch: {user.current_branch_name}</p>
              )}
              <div className="mt-3 grid gap-2">
                {(user.role === "employee" || user.role === "manager") && (
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => {
                      setMobileOpen(false);
                      router.push("/select-branch");
                    }}
                  >
                    Change branch
                  </Button>
                )}
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2"
                  onClick={() => logout().then(() => router.push("/login"))}
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        )}
        <main className="flex-1 overflow-auto bg-secondary/30 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
