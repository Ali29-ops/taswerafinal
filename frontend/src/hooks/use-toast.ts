"use client";

import * as React from "react";
import { Toast } from "@/components/ui/toast";

const TOAST_LIMIT = 3;
const TOAST_REMOVE_DELAY = 5000;

type ToasterToast = React.ComponentPropsWithoutRef<typeof Toast> & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  variant?: "default" | "destructive";
};

const actionTypes = { ADD_TOAST: "ADD_TOAST", UPDATE_TOAST: "UPDATE_TOAST", DISMISS_TOAST: "DISMISS_TOAST", REMOVE_TOAST: "REMOVE_TOAST" } as const;

let count = 0;
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

type Action =
  | { type: "ADD_TOAST"; toast: ToasterToast }
  | { type: "UPDATE_TOAST"; toast: Partial<ToasterToast> }
  | { type: "DISMISS_TOAST"; toastId?: string }
  | { type: "REMOVE_TOAST"; toastId?: string };

interface State {
  toasts: ToasterToast[];
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>();

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return { ...state, toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT) };
    case "UPDATE_TOAST":
      return { ...state, toasts: state.toasts.map((t) => (t.id === action.toast.id ? { ...t, ...action.toast } : t)) };
    case "DISMISS_TOAST": {
      const { toastId } = action;
      if (toastId) {
        const timeout = setTimeout(() => dispatch({ type: "REMOVE_TOAST", toastId }), TOAST_REMOVE_DELAY);
        toastTimeouts.set(toastId, timeout);
      }
      return { ...state, toasts: state.toasts.map((t) => (t.id === toastId || toastId === undefined ? { ...t, open: false } : t)) };
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) return { ...state, toasts: [] };
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.toastId) };
    default:
      return state;
  }
};

const listeners: Array<(state: State) => void> = [];
let memoryState: State = { toasts: [] };

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action);
  listeners.forEach((listener) => listener(memoryState));
}

export function toast({ ...props }: Omit<ToasterToast, "id">) {
  const id = genId();
  dispatch({ type: "ADD_TOAST", toast: { ...props, id, open: true, onOpenChange: (open) => !open && dispatch({ type: "DISMISS_TOAST", toastId: id }) } });
  return { id, dismiss: () => dispatch({ type: "DISMISS_TOAST", toastId: id }) };
}

export function useToast() {
  const [state, setState] = React.useState<State>(memoryState);
  React.useEffect(() => {
    listeners.push(setState);
    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) listeners.splice(index, 1);
    };
  }, [state]);
  return { ...state, toast, dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }) };
}
