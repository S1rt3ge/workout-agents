import { create } from "zustand"

import type { UserPlanSummary, WorkoutPlan } from "@/lib/api"

interface AppStoreState {
  userId: string
  currentPlan: WorkoutPlan | null
  plans: UserPlanSummary[]
  isGenerating: boolean
  setUserId: (value: string) => void
  setCurrentPlan: (plan: WorkoutPlan | null) => void
  setPlans: (plans: UserPlanSummary[]) => void
  setIsGenerating: (value: boolean) => void
}

export const useAppStore = create<AppStoreState>((set) => ({
  userId: "user-001",
  currentPlan: null,
  plans: [],
  isGenerating: false,
  setUserId: (value) => set({ userId: value }),
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  setPlans: (plans) => set({ plans }),
  setIsGenerating: (value) => set({ isGenerating: value }),
}))
