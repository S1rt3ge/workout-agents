"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"

import { getPlan } from "@/lib/api"
import { useAppStore } from "@/lib/store"

const AGENTS = [
  "information_receiver",
  "constraint_receiver",
  "exercise_selector",
  "schedule_maker",
  "progress_planner",
  "risk_assessment",
  "explainability",
  "plan_export",
]

export default function GeneratingPage() {
  const router = useRouter()

  const currentPlan = useAppStore((state) => state.currentPlan)
  const setCurrentPlan = useAppStore((state) => state.setCurrentPlan)
  const setIsGenerating = useAppStore((state) => state.setIsGenerating)

  const [activeAgentIndex, setActiveAgentIndex] = useState(0)
  const [statusText, setStatusText] = useState("Initializing pipeline...")
  const [planIdFromQuery, setPlanIdFromQuery] = useState<string | null>(null)

  useEffect(() => {
    const query = new URLSearchParams(window.location.search)
    setPlanIdFromQuery(query.get("planId"))
  }, [])

  const planId = useMemo(
    () => planIdFromQuery ?? currentPlan?.plan_id ?? null,
    [planIdFromQuery, currentPlan?.plan_id]
  )

  useEffect(() => {
    setIsGenerating(true)
    return () => setIsGenerating(false)
  }, [setIsGenerating])

  useEffect(() => {
    if (!planId) {
      setStatusText("Missing plan id. Redirecting to onboarding...")
      const timer = setTimeout(() => router.replace("/onboarding"), 900)
      return () => clearTimeout(timer)
    }

    const interval = window.setInterval(() => {
      setActiveAgentIndex((prev) => (prev + 1) % AGENTS.length)
    }, 1100)

    const poll = window.setInterval(async () => {
      const response = await getPlan(planId)
      if (response.success && response.data) {
        setCurrentPlan(response.data)
        setIsGenerating(false)
        window.clearInterval(poll)
        window.clearInterval(interval)
        router.replace(`/plan/${planId}`)
        return
      }
      setStatusText(response.error ?? "Agents are still processing...")
    }, 2000)

    return () => {
      window.clearInterval(interval)
      window.clearInterval(poll)
    }
  }, [planId, router, setCurrentPlan, setIsGenerating])

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 py-12 text-foreground">
      <div className="w-full max-w-4xl border border-border bg-card p-8">
        <p className="text-xs uppercase tracking-[0.22em] text-primary">Agent Orchestration</p>
        <h1 className="mt-3 font-heading text-4xl font-bold tracking-tight sm:text-5xl">
          Your plan is being built...
        </h1>
        <p className="mt-3 max-w-2xl text-sm text-muted-foreground">{statusText}</p>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {AGENTS.map((agent, index) => {
            const active = index === activeAgentIndex
            const completed = index < activeAgentIndex
            return (
              <div
                key={agent}
                className={`border px-4 py-4 transition ${
                  active
                    ? "border-primary bg-primary/10"
                    : completed
                      ? "border-primary/40 bg-primary/5"
                      : "border-border bg-secondary/30"
                }`}
              >
                <p className="text-xs uppercase tracking-[0.17em] text-muted-foreground">Agent {index + 1}</p>
                <p className="mt-2 text-sm font-medium">{agent}</p>
              </div>
            )
          })}
        </div>
      </div>
    </main>
  )
}
