"use client"

import { motion } from "framer-motion"
import { Activity } from "lucide-react"

export function Navbar() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="fixed inset-x-0 top-0 z-50"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Activity className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="font-heading text-lg font-bold tracking-tight text-foreground">
            WorkoutAgent
          </span>
        </div>

        <nav className="hidden items-center gap-8 md:flex">
          {["Features", "Pipeline", "Pricing"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-sm text-muted-foreground transition-colors duration-200 hover:text-foreground"
            >
              {item}
            </a>
          ))}
        </nav>

        <button className="rounded-full border border-border bg-secondary/50 px-5 py-2 text-sm font-medium text-foreground backdrop-blur-sm transition-all duration-200 hover:border-primary/50 hover:bg-secondary">
          Get Started
        </button>
      </div>
    </motion.header>
  )
}
