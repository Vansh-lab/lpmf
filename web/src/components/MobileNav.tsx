"use client";

import { useEffect, useId, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { NavList } from "@/components/NavList";

// Tailwind's md breakpoint, where the Sidebar takes over.
const DESKTOP_QUERY = "(min-width: 48rem)";

/**
 * Menu button plus a left-hand drawer holding the same page list as the
 * Sidebar, which is hidden below md. The drawer is a native modal <dialog>:
 * showModal() supplies the focus trap, Escape-to-close, the inert page
 * behind it and focus return to the button on close.
 */
export function MobileNav() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const dialogId = useId();
  const [open, setOpen] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  // The layout, and with it this state, survives navigation: close on any
  // route change, including back/forward, not only on a link click.
  const pathname = usePathname();
  const [shownPath, setShownPath] = useState(pathname);
  if (pathname !== shownPath) {
    setShownPath(pathname);
    setOpen(false);
  }

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  // A modal left open while the viewport widens past md would keep the page
  // inert behind a drawer nobody asked for.
  useEffect(() => {
    const query = window.matchMedia(DESKTOP_QUERY);
    const onChange = (e: MediaQueryListEvent) => {
      if (e.matches) setOpen(false);
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={dialogId}
        className="-ml-2 flex size-10 shrink-0 items-center justify-center rounded-md text-[color:var(--foreground)] transition hover:bg-[color:var(--border-faint)] md:hidden"
      >
        <svg
          viewBox="0 0 20 20"
          className="size-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M3 5.5h14M3 10h14M3 14.5h14" />
        </svg>
      </button>

      <dialog
        ref={dialogRef}
        id={dialogId}
        aria-label="Navigation"
        onClose={() => setOpen(false)}
        // The panel fills the dialog box, so a click whose target is the
        // dialog itself landed on the backdrop.
        onClick={(e) => {
          if (e.target === e.currentTarget) setOpen(false);
        }}
        // A literal backdrop colour: before Chrome 122 / Safari 17.4 / Firefox 120,
        // ::backdrop inherits nothing, so a theme colour (which compiles to
        // var(--color-*)) would resolve to transparent there.
        className="m-0 h-dvh max-h-none w-72 max-w-[85vw] border-0 bg-transparent p-0 text-[color:var(--foreground)] backdrop:bg-[rgb(0_0_0/0.5)]"
      >
        {open && (
          <motion.div
            initial={prefersReducedMotion ? false : { x: "-100%" }}
            animate={{ x: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 36 }}
            className="flex h-full flex-col overflow-y-auto bg-[color:var(--surface-sunken)] py-3"
            style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
          >
            <div className="flex items-center justify-between pb-3 pl-5 pr-3">
              <span className="text-sm font-semibold tracking-wide">LPMF</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="flex size-10 items-center justify-center rounded-md transition hover:bg-[color:var(--border-faint)]"
              >
                <svg
                  viewBox="0 0 20 20"
                  className="size-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M5 5l10 10M15 5L5 15" />
                </svg>
              </button>
            </div>
            <nav aria-label="Dashboard pages">
              <NavList indicatorId="drawer-active-indicator" onNavigate={() => setOpen(false)} />
            </nav>
          </motion.div>
        )}
      </dialog>
    </>
  );
}
