"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"

import { getPlan, submitFeedback, type FeedbackRequest, type WorkoutPlan } from "@/lib/api"
import { useAppStore } from "@/lib/store"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type SessionEntry = {
  weekLabel: string
  dayLabel: string
  sessionNumber: number
  exercises: Array<{ exercise_name?: string; exerciseName?: string; sets?: number; reps?: string }>
}

export default function PlanDetailsPage() {
  const params = useParams<{ planId: string }>()
  const planId = params.planId

  const setCurrentPlan = useAppStore((state) => state.setCurrentPlan)

  const [plan, setPlan] = useState<WorkoutPlan | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [activeSession, setActiveSession] = useState<SessionEntry | null>(null)
  const [feedback, setFeedback] = useState<FeedbackRequest>({
    session_number: 1,
    completed: true,
    perceived_difficulty: 3,
    notes: "",
  })
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false)
  const [feedbackResult, setFeedbackResult] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      const response = await getPlan(planId)
      if (!response.success || !response.data) {
        setLoadError(response.error ?? "Plan not found")
        setIsLoading(false)
        return
      }
      setPlan(response.data)
      setCurrentPlan(response.data)
      setIsLoading(false)
    }
    load()
  }, [planId, setCurrentPlan])

  const sessionRows = useMemo(() => {
    if (!plan) {
      return [] as SessionEntry[]
    }

    const schedule = Array.isArray(plan.weekly_schedule)
      ? plan.weekly_schedule
      : Object.entries(plan.weekly_schedule ?? {}).map(([weekLabel, days]) => ({
          week_number: Number(weekLabel.replace(/\D/g, "")) || 1,
          days: Array.isArray(days) ? days : [],
        }))

    let counter = 1
    const entries: SessionEntry[] = []
    for (const week of schedule as any[]) {
      const weekLabel = `Week ${week.week_number ?? week.weekNumber ?? "?"}`
      for (const day of week.days ?? []) {
        entries.push({
          weekLabel,
          dayLabel: day.day_name ?? day.dayName ?? "Session",
          sessionNumber: counter,
          exercises: Array.isArray(day.exercises) ? day.exercises : [],
        })
        counter += 1
      }
    }
    return entries
  }, [plan])

  const handleOpenFeedback = (entry: SessionEntry) => {
    setActiveSession(entry)
    setFeedbackResult(null)
    setFeedback({
      session_number: entry.sessionNumber,
      completed: true,
      perceived_difficulty: 3,
      notes: "",
    })
  }

  const handleSubmitFeedback = async () => {
    if (!activeSession || !plan) {
      return
    }
    setIsSubmittingFeedback(true)
    const response = await submitFeedback(plan.plan_id, feedback)
    setIsSubmittingFeedback(false)

    if (!response.success || !response.data) {
      setFeedbackResult(response.error ?? "Failed to submit feedback")
      return
    }

    setFeedbackResult(`Feedback saved (log: ${response.data.log_id})`)
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-background px-6 py-14 text-foreground">
        <div className="mx-auto max-w-5xl border border-border bg-card p-8">Loading plan...</div>
      </main>
    )
  }

  if (!plan || loadError) {
    return (
      <main className="min-h-screen bg-background px-6 py-14 text-foreground">
        <div className="mx-auto max-w-5xl border border-destructive/40 bg-destructive/10 p-8">
          <p className="font-medium">{loadError ?? "Unable to load plan"}</p>
          <Link href="/dashboard" className="mt-4 inline-block text-sm text-primary underline">
            Back to dashboard
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-background px-6 py-12 text-foreground">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-primary">Plan Detail</p>
            <h1 className="mt-2 font-heading text-4xl font-bold tracking-tight">
              Plan #{plan.plan_id.slice(0, 8)}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Created: {new Date(plan.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={plan.status} />
            <Link href="/dashboard" className="text-sm text-primary underline">
              View all plans
            </Link>
          </div>
        </div>

        <Card className="rounded-none border-border bg-card p-6 shadow-none">
          <h2 className="font-heading text-2xl font-bold">Weekly Schedule</h2>
          <div className="mt-4 grid gap-4">
            {sessionRows.map((session) => (
              <div key={session.sessionNumber} className="border border-border bg-secondary/30 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {session.weekLabel} — {session.dayLabel}
                  </p>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-none"
                        onClick={() => handleOpenFeedback(session)}
                      >
                        Session feedback
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="rounded-none border-border bg-card">
                      <DialogHeader>
                        <DialogTitle>Session #{activeSession?.sessionNumber} feedback</DialogTitle>
                        <DialogDescription>
                          Share completion and perceived difficulty for this session.
                        </DialogDescription>
                      </DialogHeader>

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="difficulty">Perceived difficulty (1-5)</Label>
                          <Input
                            id="difficulty"
                            type="number"
                            min={1}
                            max={5}
                            value={feedback.perceived_difficulty}
                            onChange={(event) =>
                              setFeedback((previous) => ({
                                ...previous,
                                perceived_difficulty: Number(event.target.value),
                              }))
                            }
                            className="rounded-none"
                          />
                        </div>

                        <div className="flex items-center gap-2">
                          <input
                            id="completed"
                            type="checkbox"
                            checked={feedback.completed}
                            onChange={(event) =>
                              setFeedback((previous) => ({
                                ...previous,
                                completed: event.target.checked,
                              }))
                            }
                          />
                          <Label htmlFor="completed">Completed session</Label>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="notes">Notes</Label>
                          <Textarea
                            id="notes"
                            value={feedback.notes}
                            onChange={(event) =>
                              setFeedback((previous) => ({
                                ...previous,
                                notes: event.target.value,
                              }))
                            }
                            className="rounded-none"
                          />
                        </div>

                        {feedbackResult && (
                          <p className="text-sm text-primary">{feedbackResult}</p>
                        )}
                      </div>

                      <DialogFooter>
                        <Button
                          className="rounded-none"
                          onClick={handleSubmitFeedback}
                          disabled={isSubmittingFeedback}
                        >
                          {isSubmittingFeedback ? "Saving..." : "Submit feedback"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>

                <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                  {session.exercises.map((exercise, index) => (
                    <li key={`${session.sessionNumber}-${index}`} className="border-l-2 border-border pl-3">
                      {exercise.exercise_name ?? exercise.exerciseName ?? "Exercise"}
                      {exercise.sets ? ` — ${exercise.sets} sets` : ""}
                      {exercise.reps ? `, ${exercise.reps} reps` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>

        <Card className="rounded-none border-border bg-card p-6 shadow-none">
          <h2 className="font-heading text-2xl font-bold">Progression Targets</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {(plan.progression_targets ?? []).map((target: any, index: number) => (
              <div key={index} className="border border-border bg-secondary/30 p-4">
                <p className="text-sm font-semibold">Week {target.week_number ?? index + 1}</p>
                <p className="mt-2 text-sm text-muted-foreground">
                  Volume x{target.volume_multiplier ?? "-"} / Intensity {target.intensity_delta_pct ?? "-"}%
                </p>
                {target.notes && <p className="mt-2 text-xs text-muted-foreground">{target.notes}</p>}
              </div>
            ))}
          </div>
        </Card>

        <Card className="rounded-none border-border bg-card p-6 shadow-none">
          <h2 className="font-heading text-2xl font-bold">Explainability</h2>
          <ul className="mt-4 space-y-3">
            {(plan.explanations ?? []).map((explanation, index) => (
              <li key={index} className="border border-border bg-secondary/30 p-4 text-sm text-muted-foreground">
                {explanation}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </main>
  )
}

function StatusBadge({ status }: { status: WorkoutPlan["status"] }) {
  if (status === "approved") {
    return <Badge className="rounded-none bg-primary/20 text-primary">Approved</Badge>
  }
  if (status === "needs_review") {
    return <Badge className="rounded-none bg-amber-500/20 text-amber-300">Needs review</Badge>
  }
  return <Badge className="rounded-none bg-destructive/20 text-red-300">Failed</Badge>
}
