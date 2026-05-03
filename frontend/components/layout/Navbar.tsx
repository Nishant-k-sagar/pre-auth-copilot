'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Sun, Moon, Menu, X } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { useState } from 'react'

const navItems = [
  { href: '/', label: 'Dashboard' },
  { href: '/analyze', label: 'Manual Entry' },
]

export function Navbar() {
  const pathname = usePathname()
  const { theme, toggleTheme } = useTheme()
  const [mobileOpen, setMobileOpen] = useState(false)
  
  return (
    <nav className="top-0 z-50 border-b border-[var(--border)] bg-[var(--card)]/70 backdrop-blur-xl">
      <div className="responsive-container flex h-10 items-center justify-between">
        <Link href="/" className="text-xs font-semibold text-[var(--foreground)]">
          Pre-Auth Copilot
        </Link>
        
        {/* Desktop navigation */}
        <div className="hidden md:flex items-center gap-4">
          {navItems.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                'text-[10px] font-medium transition-colors',
                pathname === href 
                  ? 'text-[var(--primary)]' 
                  : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
              )}
            >
              {label}
            </Link>
          ))}
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            API Docs
          </a>
          <button
            onClick={toggleTheme}
            className="rounded p-0.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="h-3 w-3" />
            ) : (
              <Moon className="h-3 w-3" />
            )}
          </button>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-1">
          <button
            onClick={toggleTheme}
            className="rounded p-0.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="h-3 w-3" />
            ) : (
              <Moon className="h-3 w-3" />
            )}
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="rounded p-0.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Toggle menu"
          >
            {mobileOpen ? (
              <X className="h-3 w-3" />
            ) : (
              <Menu className="h-3 w-3" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--border)] bg-[var(--card)]/90 backdrop-blur-xl">
          <div className="responsive-container py-1.5 space-y-0.5">
            {navItems.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  'block text-[10px] font-medium py-1 transition-colors',
                  pathname === href 
                    ? 'text-[var(--primary)]' 
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                )}
              >
                {label}
              </Link>
            ))}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMobileOpen(false)}
              className="block text-[10px] font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors py-1"
            >
              API Docs
            </a>
          </div>
        </div>
      )}
    </nav>
  )
}