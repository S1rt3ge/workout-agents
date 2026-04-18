"use client"

import { motion } from "framer-motion"
import {
  ClipboardList,
  ScanSearch,
  ShieldCheck,
  GitFork,
  Dumbbell,
  HeartPulse,
  Moon,
  FileOutput,
} from "lucide-react"

const agents = [
  {
    id: 1,
    name: "Intake Agent",
    desc: "Collects goals, history, schedule, and preferences",
    icon: ClipboardList,
  },
  {
    id: 2,
    name: "Assessment Agent",
    desc: "Evaluates fitness level and movement capacity",
    icon: ScanSearch,
  },
  {
    id: 3,
    name: "Safety Agent",
    desc: "Flags injuries, contraindications, and risk factors",
    icon: ShieldCheck,
  },
  {
    id: 4,
    name: "Split Agent",
    desc: "Designs optimal training split and frequency",
    icon: GitFork,
  },
  {
    id: 5,
    name: "Strength Agent",
    desc: "Programs compound and isolation exercises",
    icon: Dumbbell,
  },
  {
    id: 6,
    name: "Cardio Agent",
    desc: "Builds conditioning and energy system work",
    icon: HeartPulse,
  },
  {
    id: 7,
    name: "Recovery Agent",
    desc: "Manages deloads, sleep, and regeneration",
    icon: Moon,
  },
  {
    id: 8,
    name: "Output Agent",
    desc: "Compiles, validates, and delivers your final plan",
    icon: FileOutput,
  },
]

export function PipelineSection() {
  return (
    <section className="relative overflow-hidden bg-background px-6 py-32">
      {/* Subtle top divider */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-20 text-center"
        >
          <p className="mb-4 text-sm font-medium tracking-wider text-primary uppercase">
            The Pipeline
          </p>
          <h2 className="font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl text-balance">
            8 agents, one mission
          </h2>
          <p className="mx-auto mt-4 max-w-lg leading-relaxed text-muted-foreground">
            Your plan flows through a chain of specialized AI agents. Each one validates the last, ensuring nothing is missed.
          </p>
        </motion.div>

        <div className="relative">
          {/* Center vertical line */}
          <div className="absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-border md:block" />
          <motion.div
            className="absolute left-1/2 top-0 hidden w-px -translate-x-1/2 bg-primary/50 md:block"
            initial={{ height: 0 }}
            whileInView={{ height: "100%" }}
            transition={{ duration: 2, ease: "easeOut" }}
            viewport={{ once: true }}
          />

          {/* Mobile: left line */}
          <div className="absolute left-6 top-0 h-full w-px bg-border md:hidden" />
          <motion.div
            className="absolute left-6 top-0 w-px bg-primary/50 md:hidden"
            initial={{ height: 0 }}
            whileInView={{ height: "100%" }}
            transition={{ duration: 2, ease: "easeOut" }}
            viewport={{ once: true }}
          />

          <div className="flex flex-col gap-12 md:gap-16">
            {agents.map((agent, i) => {
              const isLeft = i % 2 === 0
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, x: isLeft ? -30 : 30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{
                    duration: 0.6,
                    ease: [0.22, 1, 0.36, 1],
                    delay: 0.1,
                  }}
                  viewport={{ once: true, margin: "-50px" }}
                  className={`relative flex items-center ${
                    isLeft
                      ? "md:flex-row md:pr-[calc(50%+2rem)]"
                      : "md:flex-row-reverse md:pl-[calc(50%+2rem)]"
                  }`}
                >
                  {/* Node dot on timeline */}
                  <div className="absolute left-6 z-10 hidden h-3 w-3 -translate-x-1/2 items-center justify-center md:left-1/2 md:flex">
                    <div className="h-3 w-3 rounded-full border-2 border-primary bg-background" />
                    <motion.div
                      className="absolute h-3 w-3 rounded-full bg-primary/30"
                      animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 3, repeat: Infinity, delay: i * 0.3 }}
                    />
                  </div>

                  {/* Mobile: dot on left line */}
                  <div className="absolute left-6 z-10 flex h-3 w-3 -translate-x-1/2 items-center justify-center md:hidden">
                    <div className="h-3 w-3 rounded-full border-2 border-primary bg-background" />
                  </div>

                  {/* Card */}
                  <div
                    className={`group ml-12 flex-1 md:ml-0 ${
                      isLeft ? "md:text-right" : "md:text-left"
                    }`}
                  >
                    <div
                      className={`inline-flex items-center gap-4 rounded-2xl border border-border bg-card p-6 transition-all duration-500 hover:border-primary/30 hover:shadow-[0_0_60px_rgba(0,196,140,0.06)] ${
                        isLeft ? "md:flex-row-reverse" : ""
                      }`}
                    >
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-border bg-secondary">
                        <agent.icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-primary/60">
                            0{agent.id}
                          </span>
                          <h3 className="font-heading text-lg font-bold text-foreground">
                            {agent.name}
                          </h3>
                        </div>
                        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                          {agent.desc}
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
