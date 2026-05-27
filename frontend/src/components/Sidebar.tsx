"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { logout } from "@/lib/api";
import { useMe } from "@/lib/useMe";

const NAV = [
  { href: "/dashboard", label: "Bosh sahifa", icon: "🏠", role: "all" },
  { href: "/tasks", label: "Vazifalar", icon: "✅", role: "all" },
  { href: "/attendance", label: "Davomat", icon: "🕐", role: "all" },
  { href: "/leaves", label: "Ta'til", icon: "🏖", role: "all" },
  { href: "/payroll", label: "Oylik", icon: "💰", role: "all" },
  { href: "/admin", label: "Admin panel", icon: "📊", role: "hr" },
  { href: "/employees", label: "Hodimlar", icon: "👥", role: "hr" },
  { href: "/gps", label: "GPS aniqlash", icon: "📍", role: "hr" },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const path = usePathname();
  const { me, isHR } = useMe();

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={clsx(
          "fixed inset-0 bg-black/40 z-30 lg:hidden transition-opacity",
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 flex flex-col",
          "transform transition-transform duration-200 ease-in-out",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold">H</div>
            <div>
              <div className="font-bold leading-tight">Hodim CRM</div>
              <div className="text-xs text-slate-500">v1.0</div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-500 hover:text-slate-900 p-1"
            aria-label="Yopish"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.filter((n) => n.role === "all" || isHR).map((n) => {
            const active = path === n.href || path.startsWith(n.href + "/");
            return (
              <Link
                key={n.href}
                href={n.href}
                onClick={onClose}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm",
                  active ? "bg-primary-50 text-primary-700 font-medium" : "text-slate-600 hover:bg-slate-100"
                )}
              >
                <span className="text-base">{n.icon}</span>
                {n.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-200">
          {me && (
            <div className="mb-3 text-sm">
              <div className="font-medium">{me.full_name}</div>
              <div className="text-xs text-slate-500">
                {me.role === "admin" ? "Admin" : me.role === "hr" ? "HR/Manager" : "Hodim"}
              </div>
            </div>
          )}
          <button onClick={logout} className="btn-ghost w-full text-sm">
            Chiqish
          </button>
        </div>
      </aside>
    </>
  );
}
