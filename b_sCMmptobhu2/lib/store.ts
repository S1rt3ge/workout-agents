import { create } from "zustand"

import type { GeneratePlanRequest, UserPlanSummary, WorkoutPlan } from "@/lib/api"

interface AppStoreState {
  userId: string
  currentPlan: WorkoutPlan | null
  pendingGenerateRequest: GeneratePlanRequest | null
  plans: UserPlanSummary[]
  isGenerating: boolean
  setUserId: (value: string) => void
  setCurrentPlan: (plan: WorkoutPlan | null) => void
  setPendingGenerateRequest: (request: GeneratePlanRequest | null) => void
  setPlans: (plans: UserPlanSummary[]) => void
  setIsGenerating: (value: boolean) => void
}

export const useAppStore = create<AppStoreState>((set) => ({
  userId: "user-001",
  currentPlan: null,
  pendingGenerateRequest: null,
  plans: [],
  isGenerating: false,
  setUserId: (value) => set({ userId: value }),
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  setPendingGenerateRequest: (request) => set({ pendingGenerateRequest: request }),
  setPlans: (plans) => set({ plans }),
  setIsGenerating: (value) => set({ isGenerating: value }),
}))
