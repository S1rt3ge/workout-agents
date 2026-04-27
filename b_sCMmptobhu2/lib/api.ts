export interface APIResponse<T> {
  success: boolean
  data: T | null
  error: string | null
  request_id: string
}

export interface GeneratePlanRequest {
  request_id?: string
  user_id: string
  goals: string
  age: number
  weight_kg: number
  height_cm: number
  fitness_level: "beginner" | "intermediate" | "advanced"
  training_days_per_week: number
  session_duration_minutes: number
  available_equipment: string[]
  injuries: string[]
  conditions: string[]
  restrictions: string[]
}

export interface WorkoutPlan {
  plan_id: string
  status: "approved" | "needs_review" | "failed"
  created_at: string
  week_number: number
  weekly_schedule: Record<string, any>
  progression_targets: any[]
  explanations: string[]
}

export interface UserPlanSummary {
  plan_id: string
  status: string
  created_at: string
  week_number: number
}

export interface FeedbackRequest {
  session_number: number
  completed: boolean
  perceived_difficulty: number
  notes?: string
}

export interface SessionEvent {
  request_id: string
  agent: string
  event: string
  payload: Record<string, unknown>
  timestamp: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const EQUIPMENT_MAP: Record<string, string[]> = {
  Barbell: ["barbell"],
  Dumbbells: ["dumbbells"],
  Rack: ["rack"],
  Cables: ["cable_machine"],
  "Resistance bands": ["resistance_band"],
  "Bodyweight only": ["bodyweight"],
  Kettlebell: ["kettlebell"],
  Machines: ["machines"],
}

function normalizeEquipment(items: string[]): string[] {
  return Array.from(
    new Set(
      items.flatMap((item) => EQUIPMENT_MAP[item] ?? [item.trim().toLowerCase().replace(/\s+/g, "_")])
    )
  )
}

function normalizePlan(raw: any): WorkoutPlan {
  return {
    plan_id: raw.plan_id,
    status: raw.status,
    created_at: raw.created_at,
    week_number: raw.week_number ?? raw.weeks ?? 0,
    weekly_schedule: raw.weekly_schedule ?? {},
    progression_targets: raw.progression_targets ?? [],
    explanations: Array.isArray(raw.explanations)
      ? raw.explanations.map((item: any) =>
          typeof item === "string" ? item : item?.rationale ?? JSON.stringify(item)
        )
      : [],
  }
}

function mapGenerateRequestToBackend(req: GeneratePlanRequest) {
  return {
    request_id: req.request_id,
    user_profile: {
      user_id: req.user_id,
      goals: req.goals
        .split(",")
        .map((goal) => goal.trim())
        .filter(Boolean),
      metrics: {
        age: req.age,
        weight_kg: req.weight_kg,
        height_cm: req.height_cm,
        sex: "prefer_not_to_say",
      },
      availability: {
        days_per_week: req.training_days_per_week,
        minutes_per_session: req.session_duration_minutes,
        preferred_days: [],
      },
      equipment: normalizeEquipment(req.available_equipment),
      experience_level: req.fitness_level,
      notes: null,
    },
    constraints: {
      injuries: req.injuries,
      chronic_conditions: req.conditions,
      restrictions: req.restrictions,
      contraindications: [],
    },
    weeks: 4,
    use_eval_model: false,
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
  transform?: (data: any) => T
): Promise<APIResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    })

    const payload = (await response.json()) as APIResponse<any>
    const normalizedData = payload.data
      ? transform
        ? transform(payload.data)
        : (payload.data as T)
      : null

    return {
      success: payload.success,
      data: normalizedData,
      error: payload.error,
      request_id: payload.request_id,
    }
  } catch (error) {
    return {
      success: false,
      data: null,
      error: error instanceof Error ? error.message : "Unknown API error",
      request_id: "client-error",
    }
  }
}

export async function generatePlan(
  req: GeneratePlanRequest
): Promise<APIResponse<WorkoutPlan>> {
  return request<WorkoutPlan>(
    "/v1/plans/generate",
    {
      method: "POST",
      body: JSON.stringify(mapGenerateRequestToBackend(req)),
    },
    normalizePlan
  )
}

export async function getPlan(planId: string): Promise<APIResponse<WorkoutPlan>> {
  return request<WorkoutPlan>(`/v1/plans/${planId}`, undefined, normalizePlan)
}

export async function getSessionEvents(
  requestId: string
): Promise<APIResponse<SessionEvent[]>> {
  return request<SessionEvent[]>(`/v1/sessions/${requestId}/events`)
}

export function getSessionEventsStreamUrl(requestId: string): string {
  return `${API_BASE_URL}/v1/sessions/${encodeURIComponent(requestId)}/events/stream`
}

export async function getUserPlans(
  userId: string
): Promise<APIResponse<UserPlanSummary[]>> {
  return request<UserPlanSummary[]>(
    `/v1/users/${userId}/plans`,
    undefined,
    (items: any[]) =>
      (items ?? []).map((item) => ({
        plan_id: item.plan_id,
        status: item.status,
        created_at: item.created_at,
        week_number: item.week_number,
      }))
  )
}

export async function submitFeedback(
  planId: string,
  feedback: FeedbackRequest
): Promise<APIResponse<{ log_id: string }>> {
  return request<{ log_id: string }>(`/v1/plans/${planId}/feedback`, {
    method: "POST",
    body: JSON.stringify(feedback),
  })
}
