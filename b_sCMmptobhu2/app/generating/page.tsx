"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { useRouter } from "next/navigation"

import {
  generatePlan,
  getPlan,
  getSessionEventsStreamUrl,
  type SessionEvent,
} from "@/lib/api"
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

const COMPLETION_PAUSE_MS = 900
function summarizeEvents(events: SessionEvent[]) {
  const completedAgents = new Set(
    events.filter((item) => item.event === "completed").map((item) => item.agent)
  )
  const latestStarted = events
    .slice()
    .reverse()
    .find((item) => item.event === "started" && !completedAgents.has(item.agent))

  if (completedAgents.size >= AGENTS.length) {
    return {
      activeAgentIndex: AGENTS.length,
      statusText: "All 8 agents completed. Opening your plan...",
    }
  }

  if (latestStarted) {
    const index = AGENTS.indexOf(latestStarted.agent)
    return {
      activeAgentIndex: index >= 0 ? index : 0,
      statusText: `${latestStarted.agent} is running...`,
    }
  }

  const lastCompletedIndex = Math.max(
    -1,
    ...Array.from(completedAgents).map((agent) => AGENTS.indexOf(agent))
  )
  return {
    activeAgentIndex: Math.min(lastCompletedIndex + 1, AGENTS.length - 1),
    statusText: events.length ? "Waiting for the next agent..." : "Initializing pipeline...",
  }
}

export default function GeneratingPage() {
  const router = useRouter()

  const currentPlan = useAppStore((state) => state.currentPlan)
  const pendingGenerateRequest = useAppStore((state) => state.pendingGenerateRequest)
  const setCurrentPlan = useAppStore((state) => state.setCurrentPlan)
  const setPendingGenerateRequest = useAppStore((state) => state.setPendingGenerateRequest)
  const setIsGenerating = useAppStore((state) => state.setIsGenerating)

  const [activeAgentIndex, setActiveAgentIndex] = useState(0)
  const [statusText, setStatusText] = useState("Initializing pipeline...")
  const [planIdFromQuery, setPlanIdFromQuery] = useState<string | null>(null)
  const [requestIdFromQuery, setRequestIdFromQuery] = useState<string | null>(null)

  const startedRequestRef = useRef<string | null>(null)
  const navigationStartedRef = useRef(false)
  const completionTimerRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    const query = new URLSearchParams(window.location.search)
    setPlanIdFromQuery(query.get("planId"))
    setRequestIdFromQuery(query.get("requestId"))
  }, [])

  const requestId = useMemo(
    () => requestIdFromQuery ?? pendingGenerateRequest?.request_id ?? null,
    [pendingGenerateRequest?.request_id, requestIdFromQuery]
  )

  const planId = useMemo(
    () => planIdFromQuery ?? (!requestId ? currentPlan?.plan_id ?? null : null),
    [currentPlan?.plan_id, planIdFromQuery, requestId]
  )

  useEffect(() => {
    setIsGenerating(true)
    return () => {
      setIsGenerating(false)
      if (completionTimerRef.current) {
        window.clearTimeout(completionTimerRef.current)
      }
    }
  }, [setIsGenerating])

  useEffect(() => {
    if (requestId || planId) {
      return
    }

    setStatusText("Missing generation request. Redirecting to onboarding...")
    const timer = window.setTimeout(() => router.replace("/onboarding"), 900)
    return () => window.clearTimeout(timer)
  }, [planId, requestId, router])

  useEffect(() => {
    if (!requestId || !pendingGenerateRequest || pendingGenerateRequest.request_id !== requestId) {
      return
    }
    if (startedRequestRef.current === requestId) {
      return
    }

    startedRequestRef.current = requestId
    navigationStartedRef.current = false
    setActiveAgentIndex(0)
    setStatusText("Starting 8-agent pipeline...")

    void (async () => {
      const response = await generatePlan(pendingGenerateRequest)
      if (!response.success || !response.data) {
        if (!navigationStartedRef.current) {
          setStatusText(response.error ?? "Failed to generate plan")
          setIsGenerating(false)
        }
        return
      }

      setCurrentPlan(response.data)
      setPendingGenerateRequest(null)
      if (navigationStartedRef.current) {
        return
      }

      navigationStartedRef.current = true
      setActiveAgentIndex(AGENTS.length)
      setStatusText("All 8 agents completed. Opening your plan...")
      completionTimerRef.current = window.setTimeout(() => {
        setIsGenerating(false)
        router.replace(`/plan/${response.data.plan_id}`)
      }, COMPLETION_PAUSE_MS)
    })()
  }, [
    pendingGenerateRequest,
    requestId,
    router,
    setCurrentPlan,
    setIsGenerating,
    setPendingGenerateRequest,
  ])

  useEffect(() => {
    if (!requestId) {
      return
    }

    const events: SessionEvent[] = []
    const source = new EventSource(getSessionEventsStreamUrl(requestId))

    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as SessionEvent
      events.push(event)
      const summary = summarizeEvents(events)
      setActiveAgentIndex(summary.activeAgentIndex)
      setStatusText(summary.statusText)

      const exportEvent = events.find(
        (item) => item.agent === "plan_export" && item.event === "completed"
      )
      const exportedPlanId = exportEvent?.payload.plan_id
      if (typeof exportedPlanId !== "string" || navigationStartedRef.current) {
        return
      }

      void (async () => {
        const planResponse = await getPlan(exportedPlanId)
        if (!planResponse.success || !planResponse.data || navigationStartedRef.current) {
          return
        }

        setCurrentPlan(planResponse.data)
        setPendingGenerateRequest(null)
        navigationStartedRef.current = true
        setActiveAgentIndex(AGENTS.length)
        setStatusText("All 8 agents completed. Opening your plan...")
        source.close()
        completionTimerRef.current = window.setTimeout(() => {
          setIsGenerating(false)
          router.replace(`/plan/${exportedPlanId}`)
        }, COMPLETION_PAUSE_MS)
      })()
    }

    source.addEventListener("done", () => source.close())
    source.addEventListener("timeout", () => {
      setStatusText("Session event stream timed out. Please try again.")
      source.close()
    })
    source.onerror = () => {
      setStatusText("Waiting for live session events...")
    }

    return () => {
      source.close()
    }
  }, [requestId, router, setCurrentPlan, setIsGenerating, setPendingGenerateRequest])

  useEffect(() => {
    if (requestId || !planId) {
      return
    }

    if (currentPlan?.plan_id === planId) {
      setActiveAgentIndex(AGENTS.length)
      setStatusText("All 8 agents completed. Opening your plan...")
      const timer = window.setTimeout(() => {
        setIsGenerating(false)
        router.replace(`/plan/${planId}`)
      }, COMPLETION_PAUSE_MS)
      return () => window.clearTimeout(timer)
    }

    const poll = window.setInterval(async () => {
      const response = await getPlan(planId)
      if (response.success && response.data) {
        setCurrentPlan(response.data)
        window.clearInterval(poll)
        setActiveAgentIndex(AGENTS.length)
        setStatusText("All 8 agents completed. Opening your plan...")
        completionTimerRef.current = window.setTimeout(() => {
          setIsGenerating(false)
          router.replace(`/plan/${planId}`)
        }, COMPLETION_PAUSE_MS)
        return
      }
      setStatusText(response.error ?? "Agents are still processing...")
    }, 2000)

    return () => window.clearInterval(poll)
  }, [currentPlan?.plan_id, planId, requestId, router, setCurrentPlan, setIsGenerating])

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
            const active = activeAgentIndex < AGENTS.length && index === activeAgentIndex
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
                <p className="text-xs uppercase tracking-[0.17em] text-muted-foreground">
                  Agent {index + 1}
                </p>
                <p className="mt-2 text-sm font-medium">{agent}</p>
              </div>
            )
          })}
        </div>
      </div>
    </main>
  )
}
