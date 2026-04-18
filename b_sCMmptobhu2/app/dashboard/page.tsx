"use client"

import { useEffect, useState } from "react"
import Link from "next/link"

import { getUserPlans } from "@/lib/api"
import { useAppStore } from "@/lib/store"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

export default function DashboardPage() {
  const userId = useAppStore((state) => state.userId)
  const plans = useAppStore((state) => state.plans)
  const setPlans = useAppStore((state) => state.setPlans)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      const response = await getUserPlans(userId)
      if (!response.success || !response.data) {
        setError(response.error ?? "Failed to load plans")
        setIsLoading(false)
        return
      }
      setPlans(response.data)
      setIsLoading(false)
    }
    load()
  }, [setPlans, userId])

  return (
    <main className="min-h-screen bg-background px-6 py-12 text-foreground">
      <div className="mx-auto flex max-w-5xl flex-col gap-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-primary">Dashboard</p>
            <h1 className="mt-2 font-heading text-4xl font-bold tracking-tight">Your workout plans</h1>
            <p className="mt-1 text-sm text-muted-foreground">User ID: {userId}</p>
          </div>

          <Button asChild className="rounded-none">
            <Link href="/onboarding">Generate new plan</Link>
          </Button>
        </div>

        <Card className="rounded-none border-border bg-card p-6 shadow-none">
          {isLoading && <p className="text-sm text-muted-foreground">Loading plans...</p>}

          {error && !isLoading && (
            <p className="border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive-foreground">
              {error}
            </p>
          )}

          {!isLoading && !error && plans.length === 0 && (
            <p className="text-sm text-muted-foreground">No plans yet. Generate your first one.</p>
          )}

          {!isLoading && !error && plans.length > 0 && (
            <div className="grid gap-3">
              {plans.map((plan) => (
                <Link
                  key={plan.plan_id}
                  href={`/plan/${plan.plan_id}`}
                  className="border border-border bg-secondary/30 p-4 transition hover:border-primary/50"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">Plan #{plan.plan_id.slice(0, 8)}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {new Date(plan.created_at).toLocaleString()} — {plan.week_number} weeks
                      </p>
                    </div>
                    <StatusBadge status={plan.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </main>
  )
}

function StatusBadge({ status }: { status: string }) {
  if (status === "approved") {
    return <Badge className="rounded-none bg-primary/20 text-primary">Approved</Badge>
  }
  if (status === "needs_review") {
    return <Badge className="rounded-none bg-amber-500/20 text-amber-300">Needs review</Badge>
  }
  return <Badge className="rounded-none bg-destructive/20 text-red-300">Failed</Badge>
}
