"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, MessageSquare, GitBranch, Brain, BarChart3, Moon, Sun } from "lucide-react";

export function SiteHeader() {
  const pathname = usePathname();
  const [isDark, setIsDark] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    // Theme initialization
    const isCurrentlyDark = document.documentElement.classList.contains("dark");
    setIsDark(isCurrentlyDark);

    // Scroll listener for smooth floating pill transformation
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);


  const handleToggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      document.body.classList.add("dark");
      localStorage.setItem("saarthi-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      document.body.classList.remove("dark");
      localStorage.setItem("saarthi-theme", "light");
    }
  };

  const navLinks = [
    { href: "/chat", label: "Grounded Chat", icon: MessageSquare },
    { href: "/graph", label: "Concept Graph", icon: GitBranch },
    { href: "/quiz", label: "Adaptive Quiz", icon: Brain },
    { href: "/benchmark", label: "Ablation Bench", icon: BarChart3 },
  ];

  return (
    <header
      className={`shrink-0 w-full z-40 sticky top-0 flex justify-center transition-all duration-300 ease-out ${
        isScrolled
          ? "pt-3 px-4 sm:px-6 bg-transparent pointer-events-none"
          : "pt-0 px-0 bg-white/80 dark:bg-[#06090e]/80 backdrop-blur-xl"
      }`}
    >
      <div
        className={`transition-all duration-300 ease-out flex items-center justify-between ${
          isScrolled
            ? "w-full max-w-4xl lg:max-w-5xl h-14 px-4 sm:px-6 rounded-full bg-white/85 dark:bg-[#0c111c]/85 backdrop-blur-2xl border border-zinc-200/90 dark:border-white/[0.12] shadow-xl shadow-black/5 dark:shadow-black/60 pointer-events-auto"
            : "w-full max-w-7xl h-16 px-4 sm:px-6 lg:px-8"
        }`}
      >
        
        {/* Brand / Logo */}
        <Link href="/" className="flex items-center gap-2 group shrink-0">
          <div className="h-8 w-8 rounded-xl bg-black dark:bg-white text-white dark:text-black flex items-center justify-center font-bold shadow-sm transition-transform group-hover:scale-105">
            <Sparkles className="h-4 w-4 fill-current" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-tight text-base sm:text-lg text-zinc-900 dark:text-white font-sans">
              Saarthi
            </span>
          </div>
        </Link>

        {/* Navigation items (Center) */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  isActive
                    ? "bg-zinc-100 dark:bg-white/[0.1] text-zinc-950 dark:text-white font-semibold"
                    : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-950 dark:hover:text-white"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-600 dark:text-indigo-400" : ""}`} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Actions: Moon/Sun Icon Toggle + Pill Button */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Theme Toggle Icon Button (Moon / Sun) */}
          <button
            onClick={handleToggleTheme}
            aria-label={isDark ? "Switch to white theme" : "Switch to dark theme"}
            title={isDark ? "Switch to white theme" : "Switch to dark theme"}
            className="p-2 rounded-full text-zinc-700 hover:text-black dark:text-zinc-300 dark:hover:text-white transition-colors cursor-pointer"
          >
            {isDark ? (
              <Sun className="w-5 h-5 stroke-[2]" />
            ) : (
              <Moon className="w-5 h-5 stroke-[2]" />
            )}
          </button>

          {/* Pill Action Button */}
          <Link
            href="/chat"
            className="px-4 sm:px-5 py-2 rounded-full text-xs font-semibold bg-black text-white hover:bg-zinc-800 dark:bg-zinc-200 dark:text-zinc-950 dark:hover:bg-white transition-all shadow-sm"
          >
            <span>Get Started</span>
          </Link>
        </div>

      </div>
    </header>
  );
}
