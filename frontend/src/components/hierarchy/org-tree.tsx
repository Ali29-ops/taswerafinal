"use client";

import { ChevronDown, ChevronRight, Shield, Target, User, Users } from "lucide-react";
import { useState } from "react";
import { HierarchyNode } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";

function roleIcon(role: string) {
  if (role === "admin") return Shield;
  if (role === "manager") return Users;
  if (role === "group") return Users;
  return User;
}

function roleLabel(role: string) {
  if (role === "admin") return "Admin";
  if (role === "manager") return "Manager";
  if (role === "group") return "Group";
  if (role === "employee") return "Employee";
  return role;
}

function ProgressBar({ value, met }: { value: number; met?: boolean }) {
  return (
    <div className="flex min-w-[120px] items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
        <div
          className={cn("h-full transition-all", met ? "bg-green-600" : "bg-foreground")}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className="w-10 text-right text-xs font-medium">{value}%</span>
    </div>
  );
}

function TreeNode({ node, depth = 0 }: { node: HierarchyNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children.length > 0;
  const Icon = roleIcon(node.role);
  const isEmployee = node.role === "employee";

  return (
    <div>
      <div
        className={cn(
          "flex flex-wrap items-center gap-3 rounded-lg border border-border bg-white px-4 py-3",
          depth > 0 && "ml-6"
        )}
        style={{ marginLeft: depth > 0 ? depth * 24 : 0 }}
      >
        {hasChildren ? (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded hover:bg-secondary"
            aria-label={open ? "Collapse" : "Expand"}
          >
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="w-6 shrink-0" />
        )}

        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
          <Icon className="h-4 w-4" />
        </div>

        <div className="min-w-[160px] flex-1">
          <p className="font-medium">{node.name}</p>
          <p className="text-xs capitalize text-muted-foreground">{roleLabel(node.role)}</p>
        </div>

        {isEmployee && (
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Target className="h-3.5 w-3.5" />
              <span>
                {node.photos_printed} / {node.target_photos > 0 ? node.target_photos : "—"} photos
              </span>
            </div>
            {node.target_photos > 0 ? (
              <ProgressBar value={node.progress_percent} met={node.target_met} />
            ) : (
              <span className="text-xs text-muted-foreground">No target set</span>
            )}
            {node.target_met && (
              <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                Target met
              </span>
            )}
            <span className="font-medium">{formatCurrency(node.total_commission)}</span>
          </div>
        )}

        {node.role === "manager" && (
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <span>
              Team: {node.team_photos_printed} / {node.team_target_photos > 0 ? node.team_target_photos : "—"} photos
            </span>
            {node.team_target_photos > 0 && (
              <ProgressBar value={node.team_progress_percent} />
            )}
            <span>{node.children.length} employee{node.children.length !== 1 ? "s" : ""}</span>
          </div>
        )}
      </div>

      {open && hasChildren && (
        <div className="mt-2 space-y-2 border-l-2 border-border pl-2" style={{ marginLeft: depth * 24 + 12 }}>
          {node.children.map((child) => (
            <TreeNode key={`${child.role}-${child.id}`} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function OrgTree({ tree }: { tree: HierarchyNode }) {
  return (
    <div className="space-y-2">
      <TreeNode node={tree} depth={0} />
    </div>
  );
}
