import { NavList } from "@/components/NavList";

/** Desktop navigation; below md the Topbar's MobileNav drawer replaces it. */
export function Sidebar() {
  return (
    <nav
      aria-label="Dashboard pages"
      className="hidden h-full w-64 shrink-0 flex-col overflow-y-auto bg-[color:var(--surface-sunken)] py-4 md:flex"
      style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
    >
      <div className="px-5 pb-4 text-sm font-semibold tracking-wide text-[color:var(--foreground)]">
        LPMF
      </div>
      <NavList indicatorId="sidebar-active-indicator" />
    </nav>
  );
}
