"use client"

import { motion } from "framer-motion"
import { ArrowRight, Activity } from "lucide-react"

export function CTASection() {
  return (
    <section className="relative bg-background px-6 py-32">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

      <div className="mx-auto max-w-3xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          viewport={{ once: true }}
          className="flex flex-col items-center gap-8"
        >
          <h2 className="font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl text-balance">
            Your next program
            <br />
            <span className="text-primary">starts here.</span>
          </h2>
          <p className="max-w-md leading-relaxed text-muted-foreground">
            Join thousands of athletes training smarter with AI agents that understand progressive overload, periodization, and recovery.
          </p>
          <button className="group inline-flex items-center gap-3 rounded-full bg-primary px-8 py-4 text-base font-semibold text-primary-foreground transition-all duration-300 hover:shadow-[0_0_40px_rgba(0,196,140,0.3)] hover:scale-[1.02] active:scale-[0.98]">
            Build my plan
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </button>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="mx-auto mt-32 max-w-6xl">
        <div className="absolute inset-x-6 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
        <div className="flex flex-col items-center justify-between gap-6 pt-10 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <Activity className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-heading text-sm font-bold tracking-tight text-foreground">
              WorkoutAgent
            </span>
          </div>
          <p className="text-xs text-muted-foreground/60">
            Built with multi-agent AI. Designed for serious athletes.
          </p>
        </div>
      </div>
    </section>
  )
}
