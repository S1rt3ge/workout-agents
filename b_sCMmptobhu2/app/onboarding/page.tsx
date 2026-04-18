"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"

import { generatePlan, type GeneratePlanRequest } from "@/lib/api"
import { useAppStore } from "@/lib/store"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"

type FitnessLevel = "beginner" | "intermediate" | "advanced"

interface FormState {
  goals: string
  age: number
  weight_kg: number
  height_cm: number
  fitness_level: FitnessLevel
  training_days_per_week: number
  session_duration_minutes: number
  available_equipment: string[]
  injuries: string
  conditions: string
  restrictions: string
}

const TOTAL_STEPS = 5

const GOAL_OPTIONS = [
  "Build muscle",
  "Lose fat",
  "Improve endurance",
  "General fitness",
]

const FITNESS_LEVEL_OPTIONS: FitnessLevel[] = ["beginner", "intermediate", "advanced"]
const TRAINING_DAYS_OPTIONS = [2, 3, 4, 5]
const SESSION_DURATION_OPTIONS = [30, 45, 60, 90]
const EQUIPMENT_OPTIONS = [
  "Barbell",
  "Dumbbells",
  "Rack",
  "Cables",
  "Resistance bands",
  "Bodyweight only",
  "Kettlebell",
  "Machines",
]

export default function OnboardingPage() {
  const router = useRouter()
  const userId = useAppStore((state) => state.userId)
  const setCurrentPlan = useAppStore((state) => state.setCurrentPlan)
  const setIsGenerating = useAppStore((state) => state.setIsGenerating)

  const [step, setStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const [form, setForm] = useState<FormState>({
    goals: "",
    age: 28,
    weight_kg: 75,
    height_cm: 175,
    fitness_level: "intermediate",
    training_days_per_week: 4,
    session_duration_minutes: 60,
    available_equipment: ["Barbell", "Dumbbells"],
    injuries: "",
    conditions: "",
    restrictions: "",
  })

  const progressValue = useMemo(() => (step / TOTAL_STEPS) * 100, [step])

  const updateForm = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((previous) => ({ ...previous, [key]: value }))
  }

  const toggleEquipment = (item: string, checked: boolean) => {
    setForm((previous) => {
      const values = new Set(previous.available_equipment)
      if (checked) {
        values.add(item)
      } else {
        values.delete(item)
      }
      return { ...previous, available_equipment: Array.from(values) }
    })
  }

  const goNext = async () => {
    if (step < TOTAL_STEPS) {
      setStep((value) => value + 1)
      return
    }

    setErrorMessage(null)
    setIsSubmitting(true)
    setIsGenerating(true)

    const payload: GeneratePlanRequest = {
      user_id: userId,
      goals: form.goals,
      age: form.age,
      weight_kg: form.weight_kg,
      height_cm: form.height_cm,
      fitness_level: form.fitness_level,
      training_days_per_week: form.training_days_per_week,
      session_duration_minutes: form.session_duration_minutes,
      available_equipment: form.available_equipment,
      injuries: splitCommaSeparated(form.injuries),
      conditions: splitCommaSeparated(form.conditions),
      restrictions: splitCommaSeparated(form.restrictions),
    }

    const response = await generatePlan(payload)
    setIsSubmitting(false)
    setIsGenerating(false)

    if (!response.success || !response.data) {
      setErrorMessage(response.error ?? "Failed to generate plan")
      return
    }

    setCurrentPlan(response.data)
    router.push(`/generating?planId=${response.data.plan_id}`)
  }

  const goBack = () => {
    setErrorMessage(null)
    if (step > 1) {
      setStep((value) => value - 1)
    }
  }

  return (
    <main className="min-h-screen bg-background px-6 py-12 text-foreground">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.22em] text-primary">Onboarding</p>
          <h1 className="font-heading text-4xl font-bold tracking-tight sm:text-5xl">
            Build your personalized workout profile
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Answer a few focused questions. The 8-agent pipeline will use this profile to generate a safe and tailored plan.
          </p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs uppercase tracking-[0.16em] text-muted-foreground">
            <span>Step {step} of {TOTAL_STEPS}</span>
            <span>{Math.round(progressValue)}%</span>
          </div>
          <Progress value={progressValue} className="h-2 rounded-none" />
        </div>

        <Card className="rounded-none border-border bg-card p-6 shadow-none sm:p-8">
          {step === 1 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="goal-input">What&apos;s your main goal?</Label>
                <Input
                  id="goal-input"
                  value={form.goals}
                  onChange={(event) => updateForm("goals", event.target.value)}
                  placeholder="Example: Build muscle, lose fat"
                  className="rounded-none"
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {GOAL_OPTIONS.map((goal) => {
                  const selected = form.goals.toLowerCase().includes(goal.toLowerCase())
                  return (
                    <button
                      key={goal}
                      type="button"
                      onClick={() => updateForm("goals", goal)}
                      className={`border p-4 text-left transition ${
                        selected
                          ? "border-primary bg-primary/10 text-foreground"
                          : "border-border bg-secondary/40 text-muted-foreground hover:border-primary/50"
                      }`}
                    >
                      <span className="font-medium">{goal}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <MetricInput
                  label="Age"
                  value={form.age}
                  min={13}
                  max={100}
                  onChange={(value) => updateForm("age", value)}
                />
                <MetricInput
                  label="Weight (kg)"
                  value={form.weight_kg}
                  min={30}
                  max={350}
                  onChange={(value) => updateForm("weight_kg", value)}
                />
                <MetricInput
                  label="Height (cm)"
                  value={form.height_cm}
                  min={100}
                  max={250}
                  onChange={(value) => updateForm("height_cm", value)}
                />
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium">Fitness level</p>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {FITNESS_LEVEL_OPTIONS.map((level) => {
                    const selected = form.fitness_level === level
                    return (
                      <button
                        key={level}
                        type="button"
                        onClick={() => updateForm("fitness_level", level)}
                        className={`border px-4 py-3 text-left uppercase transition ${
                          selected
                            ? "border-primary bg-primary/10 text-foreground"
                            : "border-border bg-secondary/40 text-muted-foreground hover:border-primary/50"
                        }`}
                      >
                        {level}
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <SelectorRow
                title="Training days per week"
                options={TRAINING_DAYS_OPTIONS.map(String)}
                selected={String(form.training_days_per_week)}
                onSelect={(value) => updateForm("training_days_per_week", Number(value))}
              />

              <SelectorRow
                title="Session duration (minutes)"
                options={SESSION_DURATION_OPTIONS.map(String)}
                selected={String(form.session_duration_minutes)}
                onSelect={(value) => updateForm("session_duration_minutes", Number(value))}
              />
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm font-medium">Select available equipment</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {EQUIPMENT_OPTIONS.map((item) => {
                  const checked = form.available_equipment.includes(item)
                  return (
                    <label
                      key={item}
                      className={`flex cursor-pointer items-center gap-3 border p-3 transition ${
                        checked
                          ? "border-primary bg-primary/10"
                          : "border-border bg-secondary/40 hover:border-primary/40"
                      }`}
                    >
                      <Checkbox
                        checked={checked}
                        onCheckedChange={(value) => toggleEquipment(item, Boolean(value))}
                      />
                      <span className="text-sm">{item}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-5 border border-primary/40 bg-primary/10 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-primary">Health &amp; Safety</p>
              <p className="text-sm text-muted-foreground">
                This information is used to keep you safe. Every exercise will be checked against these.
              </p>

              <FormTextInput
                label="Injuries (comma separated)"
                value={form.injuries}
                onChange={(value) => updateForm("injuries", value)}
                placeholder="Example: left_knee_pain, shoulder_impingement"
              />

              <FormTextInput
                label="Chronic conditions"
                value={form.conditions}
                onChange={(value) => updateForm("conditions", value)}
                placeholder="Example: hypertension"
              />

              <FormTextInput
                label="Restrictions"
                value={form.restrictions}
                onChange={(value) => updateForm("restrictions", value)}
                placeholder="Example: avoid deep knee flexion"
              />
            </div>
          )}

          {errorMessage && (
            <p className="mt-6 border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive-foreground">
              {errorMessage}
            </p>
          )}

          <div className="mt-8 flex items-center justify-between">
            <Button
              type="button"
              variant="outline"
              className="rounded-none"
              onClick={goBack}
              disabled={step === 1 || isSubmitting}
            >
              Back
            </Button>

            <Button
              type="button"
              className="rounded-none"
              onClick={goNext}
              disabled={isSubmitting || !form.goals.trim()}
            >
              {step === TOTAL_STEPS
                ? isSubmitting
                  ? "Generating..."
                  : "Generate Plan"
                : "Next"}
            </Button>
          </div>
        </Card>
      </div>
    </main>
  )
}

function splitCommaSeparated(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
}

function MetricInput({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  onChange: (value: number) => void
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(Number(event.target.value))}
        className="rounded-none"
      />
    </div>
  )
}

function SelectorRow({
  title,
  options,
  selected,
  onSelect,
}: {
  title: string
  options: string[]
  selected: string
  onSelect: (value: string) => void
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">{title}</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {options.map((option) => {
          const active = selected === option
          return (
            <button
              key={option}
              type="button"
              onClick={() => onSelect(option)}
              className={`border px-4 py-3 text-sm font-medium transition ${
                active
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border bg-secondary/40 text-muted-foreground hover:border-primary/50"
              }`}
            >
              {option}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function FormTextInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="rounded-none border-primary/30 bg-background/70"
      />
    </div>
  )
}
