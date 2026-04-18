"use client"

import { motion } from "framer-motion"
import { Shield, Brain, TrendingUp, Zap, Activity, Target } from "lucide-react"

const agentNodes = [
  { label: "Intake", x: 10, y: 50 },
  { label: "Assessment", x: 25, y: 25 },
  { label: "Safety", x: 40, y: 55 },
  { label: "Split", x: 55, y: 30 },
  { label: "Strength", x: 65, y: 60 },
  { label: "Cardio", x: 75, y: 25 },
  { label: "Recovery", x: 85, y: 50 },
  { label: "Output", x: 95, y: 40 },
]

const connections = [
  [0, 1], [0, 2], [1, 3], [2, 3], [3, 4], [3, 5], [4, 6], [5, 6], [6, 7],
]

function PipelineAnimation() {
  return (
    <div className="relative h-48 w-full overflow-hidden sm:h-56">
      <svg
        viewBox="0 0 110 80"
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Connection lines */}
        {connections.map(([from, to], i) => {
          const f = agentNodes[from]
          const t = agentNodes[to]
          return (
            <g key={`line-${i}`}>
              <line
                x1={f.x}
                y1={f.y}
                x2={t.x}
                y2={t.y}
                stroke="#222"
                strokeWidth="0.5"
              />
              <motion.line
                x1={f.x}
                y1={f.y}
                x2={t.x}
                y2={t.y}
                stroke="#00C48C"
                strokeWidth="0.5"
                strokeDasharray="3 6"
                initial={{ strokeDashoffset: 9 }}
                animate={{ strokeDashoffset: 0 }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "linear",
                  delay: i * 0.15,
                }}
              />
            </g>
          )
        })}

        {/* Nodes */}
        {agentNodes.map((node, i) => (
          <motion.g
            key={node.label}
            initial={{ opacity: 0, scale: 0 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08, duration: 0.5 }}
            viewport={{ once: true }}
          >
            <circle
              cx={node.x}
              cy={node.y}
              r="4"
              fill="#111"
              stroke="#00C48C"
              strokeWidth="0.6"
            />
            <motion.circle
              cx={node.x}
              cy={node.y}
              r="4"
              fill="transparent"
              stroke="#00C48C"
              strokeWidth="0.3"
              initial={{ r: 4 }}
              animate={{ r: 7, opacity: [0.4, 0] }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
            <text
              x={node.x}
              y={node.y + 9}
              textAnchor="middle"
              fill="#888"
              fontSize="2.8"
              fontFamily="sans-serif"
            >
              {node.label}
            </text>
          </motion.g>
        ))}
      </svg>
    </div>
  )
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.15,
    },
  },
}

const cardVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  },
}

export function FeaturesSection() {
  return (
    <section className="relative bg-background px-6 py-32">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16 text-center"
        >
          <p className="mb-4 text-sm font-medium tracking-wider text-primary uppercase">
            How it works
          </p>
          <h2 className="font-heading text-4xl font-bold tracking-tight text-foreground sm:text-5xl text-balance">
            Intelligence at every step
          </h2>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 gap-4 lg:grid-cols-3 lg:grid-rows-2"
        >
          {/* Large card — Safety Gate pipeline */}
          <motion.div
            variants={cardVariants}
            className="group relative col-span-1 row-span-2 overflow-hidden rounded-2xl border border-border bg-card p-8 transition-all duration-500 hover:border-primary/30 hover:shadow-[0_0_60px_rgba(0,196,140,0.06)] lg:col-span-2"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <div className="relative z-10">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl border border-border bg-secondary p-3">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading mb-2 text-2xl font-bold text-foreground">
                Safety Gate Pipeline
              </h3>
              <p className="mb-8 max-w-md leading-relaxed text-muted-foreground">
                Every plan passes through our multi-agent safety pipeline. 8 specialized agents validate, refine, and protect your training.
              </p>
              <PipelineAnimation />
            </div>
          </motion.div>

          {/* Small card — 8 Specialized Agents */}
          <motion.div
            variants={cardVariants}
            className="group relative overflow-hidden rounded-2xl border border-border bg-card p-8 transition-all duration-500 hover:border-primary/30 hover:shadow-[0_0_60px_rgba(0,196,140,0.06)]"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <div className="relative z-10">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl border border-border bg-secondary p-3">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading mb-2 text-xl font-bold text-foreground">
                8 Specialized Agents
              </h3>
              <p className="leading-relaxed text-muted-foreground">
                Each agent masters one domain — from injury prevention to progressive overload. They collaborate, not compromise.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {["Intake", "Safety", "Strength", "Cardio", "Recovery", "Nutrition", "Progression", "Output"].map(
                  (agent) => (
                    <span
                      key={agent}
                      className="rounded-full border border-border bg-secondary/50 px-3 py-1 text-xs text-muted-foreground"
                    >
                      {agent}
                    </span>
                  )
                )}
              </div>
            </div>
          </motion.div>

          {/* Small card — Week-by-week Progression */}
          <motion.div
            variants={cardVariants}
            className="group relative overflow-hidden rounded-2xl border border-border bg-card p-8 transition-all duration-500 hover:border-primary/30 hover:shadow-[0_0_60px_rgba(0,196,140,0.06)]"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <div className="relative z-10">
              <div className="mb-4 inline-flex items-center justify-center rounded-xl border border-border bg-secondary p-3">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <h3 className="font-heading mb-2 text-xl font-bold text-foreground">
                Week-by-week Progression
              </h3>
              <p className="leading-relaxed text-muted-foreground">
                Plans evolve with you. Volume, intensity, and recovery adapt based on real feedback — not static templates.
              </p>
              {/* Mini chart visual */}
              <div className="mt-6 flex items-end gap-1.5">
                {[30, 40, 35, 50, 55, 65, 60, 75, 80, 85, 78, 90].map((h, i) => (
                  <motion.div
                    key={i}
                    initial={{ height: 0 }}
                    whileInView={{ height: `${h}%` }}
                    transition={{ delay: i * 0.05, duration: 0.5 }}
                    viewport={{ once: true }}
                    className="w-full max-w-3 rounded-sm bg-primary/20"
                    style={{ minHeight: 4 }}
                  >
                    <div
                      className="w-full rounded-sm bg-primary/60"
                      style={{ height: "40%" }}
                    />
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Secondary features row */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
        >
          {[
            {
              icon: Zap,
              title: "Instant Generation",
              desc: "Full plans in under 10 seconds. Multi-agent orchestration runs in parallel.",
            },
            {
              icon: Activity,
              title: "Injury-Aware",
              desc: "Safety agents flag contraindicated movements and suggest alternatives automatically.",
            },
            {
              icon: Target,
              title: "Goal-Specific",
              desc: "Hypertrophy, strength, endurance, or rehab. Your goal shapes every variable.",
            },
          ].map((feature) => (
            <motion.div
              key={feature.title}
              variants={cardVariants}
              className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 transition-all duration-500 hover:border-primary/30 hover:shadow-[0_0_60px_rgba(0,196,140,0.06)]"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
              <div className="relative z-10">
                <div className="mb-3 inline-flex items-center justify-center rounded-xl border border-border bg-secondary p-2.5">
                  <feature.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="font-heading mb-1.5 text-base font-bold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
