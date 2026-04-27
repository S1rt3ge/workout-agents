"""Seed script for populating the exercises collection with baseline data."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workout_agent.core.config import get_settings


EXERCISES: list[dict[str, Any]] = [
    {
        "name": "Barbell Back Squat",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        "equipment": ["barbell", "rack"],
        "difficulty": "intermediate",
        "contraindications": ["knee_injury", "lower_back_pain"],
        "instructions": "Place the bar across your upper back and squat to a controlled depth. Keep your chest up and drive through mid-foot to stand.",
        "category": "strength",
    },
    {
        "name": "Romanian Deadlift",
        "muscle_groups": ["hamstrings", "glutes", "lower_back"],
        "equipment": ["barbell"],
        "difficulty": "intermediate",
        "contraindications": ["lower_back_pain", "hamstring_strain"],
        "instructions": "Hinge at the hips while keeping the bar close to your legs and spine neutral. Lower to hamstring tension, then return by squeezing glutes.",
        "category": "strength",
    },
    {
        "name": "Dumbbell Bench Press",
        "muscle_groups": ["chest", "triceps", "front_delts"],
        "equipment": ["dumbbells", "bench"],
        "difficulty": "beginner",
        "contraindications": ["shoulder_impingement", "wrist_pain"],
        "instructions": "Press dumbbells from chest level to full arm extension with control. Keep shoulder blades lightly retracted throughout the set.",
        "category": "strength",
    },
    {
        "name": "Pull-Up",
        "muscle_groups": ["lats", "biceps", "upper_back"],
        "equipment": ["pull_up_bar"],
        "difficulty": "advanced",
        "contraindications": ["elbow_tendinopathy", "shoulder_pain"],
        "instructions": "Hang from the bar and pull your chest toward it without swinging. Lower under control to full extension before the next rep.",
        "category": "strength",
    },
    {
        "name": "Walking Lunge",
        "muscle_groups": ["quadriceps", "glutes", "adductors"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["knee_injury", "ankle_instability"],
        "instructions": "Step forward into a lunge and lower until both knees are bent. Push through the front foot and continue alternating steps.",
        "category": "strength",
    },
    {
        "name": "Plank",
        "muscle_groups": ["core", "transverse_abdominis", "shoulders"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["shoulder_pain", "postpartum_early_phase"],
        "instructions": "Hold a straight line from head to heels on forearms and toes. Brace the abdomen and avoid letting the hips sag.",
        "category": "strength",
    },
    {
        "name": "Seated Cable Row",
        "muscle_groups": ["mid_back", "lats", "biceps"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Pull the handle toward your torso while keeping shoulders down and chest tall. Extend arms slowly to maintain tension.",
        "category": "strength",
    },
    {
        "name": "Kettlebell Swing",
        "muscle_groups": ["glutes", "hamstrings", "core"],
        "equipment": ["kettlebell"],
        "difficulty": "intermediate",
        "contraindications": ["lower_back_pain", "shoulder_instability"],
        "instructions": "Hinge at the hips and snap through to swing the kettlebell to chest height. Let the bell return naturally while maintaining a neutral spine.",
        "category": "hiit",
    },
    {
        "name": "Stationary Bike Intervals",
        "muscle_groups": ["quadriceps", "glutes", "calves"],
        "equipment": ["stationary_bike"],
        "difficulty": "beginner",
        "contraindications": ["severe_knee_pain"],
        "instructions": "Alternate short high-intensity efforts with easy pedaling recovery. Keep cadence smooth and posture upright.",
        "category": "cardio",
    },
    {
        "name": "Jump Rope",
        "muscle_groups": ["calves", "shoulders", "cardiorespiratory_system"],
        "equipment": ["jump_rope"],
        "difficulty": "intermediate",
        "contraindications": ["achilles_tendinopathy", "ankle_injury"],
        "instructions": "Perform light, rhythmic jumps while rotating the rope from your wrists. Land softly and keep jumps low to reduce impact.",
        "category": "cardio",
    },
    {
        "name": "Treadmill Incline Walk",
        "muscle_groups": ["glutes", "calves", "hamstrings"],
        "equipment": ["treadmill"],
        "difficulty": "beginner",
        "contraindications": ["severe_hip_pain"],
        "instructions": "Walk at a brisk pace on a moderate incline while maintaining stable posture. Use a conversational effort level unless interval work is prescribed.",
        "category": "cardio",
    },
    {
        "name": "Burpee",
        "muscle_groups": ["chest", "quadriceps", "core", "shoulders"],
        "equipment": ["bodyweight"],
        "difficulty": "advanced",
        "contraindications": ["wrist_pain", "knee_injury", "hypertension_uncontrolled"],
        "instructions": "Drop to a plank, perform a push-up if needed, then jump feet in and explode upward. Keep movement crisp while preserving form.",
        "category": "hiit",
    },
    {
        "name": "Mountain Climber",
        "muscle_groups": ["core", "hip_flexors", "shoulders"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["wrist_pain", "shoulder_instability"],
        "instructions": "From a plank, drive knees alternately toward the chest at a controlled pace. Keep hips steady and avoid excessive bouncing.",
        "category": "hiit",
    },
    {
        "name": "Rowing Ergometer",
        "muscle_groups": ["legs", "back", "cardiorespiratory_system"],
        "equipment": ["rowing_machine"],
        "difficulty": "intermediate",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Drive with the legs first, then swing and pull with the arms in one fluid stroke. Reverse the sequence smoothly on recovery.",
        "category": "cardio",
    },
    {
        "name": "Single-Leg Glute Bridge",
        "muscle_groups": ["glutes", "hamstrings", "core"],
        "equipment": ["bodyweight"],
        "difficulty": "intermediate",
        "contraindications": ["hip_impingement", "acute_lower_back_pain"],
        "instructions": "Press through one heel to lift hips while keeping pelvis level. Lower slowly and repeat before switching sides.",
        "category": "strength",
    },
    {
        "name": "Bird Dog",
        "muscle_groups": ["core", "glutes", "lower_back"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["acute_wrist_pain"],
        "instructions": "From hands and knees, extend opposite arm and leg while keeping trunk stable. Pause briefly, then return and alternate sides.",
        "category": "flexibility",
    },
    {
        "name": "Standing Hamstring Stretch",
        "muscle_groups": ["hamstrings", "calves"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["acute_hamstring_strain"],
        "instructions": "Place one heel on a low surface and hinge gently from the hips. Hold a mild stretch without bouncing.",
        "category": "flexibility",
    },
    {
        "name": "Child's Pose",
        "muscle_groups": ["lower_back", "lats", "hips"],
        "equipment": ["bodyweight", "mat"],
        "difficulty": "beginner",
        "contraindications": ["knee_pain_severe"],
        "instructions": "Sit hips back toward heels and reach arms forward on the floor. Breathe slowly and relax into a comfortable range.",
        "category": "flexibility",
    },
    {
        "name": "Band Shoulder External Rotation",
        "muscle_groups": ["rotator_cuff", "rear_delts"],
        "equipment": ["resistance_band"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_inflammation"],
        "instructions": "Keep elbow tucked at your side and rotate the forearm outward against band tension. Move slowly and avoid shrugging.",
        "category": "strength",
    },
    {
        "name": "Farmer Carry",
        "muscle_groups": ["grip", "traps", "core", "glutes"],
        "equipment": ["dumbbells", "kettlebells"],
        "difficulty": "intermediate",
        "contraindications": ["hand_injury", "acute_lower_back_pain"],
        "instructions": "Walk with weights at your sides while maintaining tall posture and braced core. Use short controlled steps and steady breathing.",
        "category": "strength",
    },
    {
        "name": "Goblet Squat",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["dumbbells", "kettlebell"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain"],
        "instructions": "Hold one weight at chest height and squat with an upright torso. Keep pressure even through the feet and stand tall at the top.",
        "category": "strength",
    },
    {
        "name": "Dumbbell Romanian Deadlift",
        "muscle_groups": ["hamstrings", "glutes", "core"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Hinge at the hips with dumbbells close to the legs and a neutral spine. Lower with control, then stand by driving hips forward.",
        "category": "strength",
    },
    {
        "name": "Dumbbell Overhead Press",
        "muscle_groups": ["shoulders", "triceps", "upper_chest"],
        "equipment": ["dumbbells"],
        "difficulty": "intermediate",
        "contraindications": ["shoulder_impingement", "acute_neck_pain"],
        "instructions": "Press dumbbells overhead from shoulder height without arching the lower back. Lower with control and keep ribs stacked over hips.",
        "category": "strength",
    },
    {
        "name": "Incline Dumbbell Press",
        "muscle_groups": ["upper_chest", "front_delts", "triceps"],
        "equipment": ["dumbbells", "bench"],
        "difficulty": "intermediate",
        "contraindications": ["shoulder_pain"],
        "instructions": "Press dumbbells from an incline bench to full extension while maintaining shoulder control. Lower until elbows are just below the bench line.",
        "category": "strength",
    },
    {
        "name": "One-Arm Dumbbell Row",
        "muscle_groups": ["lats", "mid_back", "biceps"],
        "equipment": ["dumbbells", "bench"],
        "difficulty": "beginner",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Brace one hand on a bench and row the dumbbell toward your hip. Pause at the top and lower slowly.",
        "category": "strength",
    },
    {
        "name": "Lat Pulldown",
        "muscle_groups": ["lats", "biceps", "upper_back"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["shoulder_pain"],
        "instructions": "Pull the bar toward the top of the chest while keeping the torso stable. Control the return to full arm extension.",
        "category": "strength",
    },
    {
        "name": "Leg Press",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain", "lower_back_pain"],
        "instructions": "Press the platform away while keeping hips and low back stable in the seat. Lower with control until a comfortable knee angle.",
        "category": "strength",
    },
    {
        "name": "Leg Curl Machine",
        "muscle_groups": ["hamstrings"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain"],
        "instructions": "Curl the pad toward the glutes without lifting the hips. Pause briefly, then return slowly.",
        "category": "strength",
    },
    {
        "name": "Cable Chest Fly",
        "muscle_groups": ["chest", "front_delts"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["shoulder_instability"],
        "instructions": "Bring both handles together in a hugging arc while keeping a slight bend in the elbows. Return slowly until the chest is stretched.",
        "category": "strength",
    },
    {
        "name": "Cable Face Pull",
        "muscle_groups": ["rear_delts", "upper_back", "rotator_cuff"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_inflammation"],
        "instructions": "Pull the rope toward eye level with elbows high and wide. Squeeze the upper back and return with control.",
        "category": "strength",
    },
    {
        "name": "Step-Up",
        "muscle_groups": ["quadriceps", "glutes", "calves"],
        "equipment": ["bodyweight", "dumbbells", "bench"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain", "ankle_instability"],
        "instructions": "Step onto a stable box or bench and drive through the full foot to stand tall. Lower with control and alternate sides.",
        "category": "strength",
    },
    {
        "name": "Hip Thrust",
        "muscle_groups": ["glutes", "hamstrings", "core"],
        "equipment": ["barbell", "bench"],
        "difficulty": "intermediate",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Drive hips upward from a bench-supported position until hips are fully extended. Lower slowly while keeping ribs down.",
        "category": "strength",
    },
    {
        "name": "Pallof Press",
        "muscle_groups": ["core", "obliques"],
        "equipment": ["cable_machine", "resistance_band"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_pain"],
        "instructions": "Press the handle or band straight out from the chest and resist rotation. Hold briefly, then return with control.",
        "category": "strength",
    },
    {
        "name": "Dead Bug",
        "muscle_groups": ["core", "transverse_abdominis", "hip_flexors"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["acute_hip_flexor_strain"],
        "instructions": "Lower the opposite arm and leg toward the floor while keeping the ribs down. Return and alternate sides without arching the back.",
        "category": "strength",
    },
    {
        "name": "Push-Up",
        "muscle_groups": ["chest", "triceps", "front_delts", "core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["wrist_pain", "shoulder_pain"],
        "instructions": "Lower your body in one line until the chest nears the floor, then press back up. Keep the trunk braced and elbows controlled.",
        "category": "strength",
    },
    {
        "name": "Resistance Band Row",
        "muscle_groups": ["lats", "mid_back", "biceps"],
        "equipment": ["resistance_band"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_pain"],
        "instructions": "Pull the band handles toward the torso while squeezing the shoulder blades together. Return slowly to starting tension.",
        "category": "strength",
    },
    {
        "name": "Glute Bridge",
        "muscle_groups": ["glutes", "hamstrings", "core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Lift hips until shoulders, hips, and knees form a line. Pause briefly and lower under control.",
        "category": "strength",
    },
    {
        "name": "Wall Sit",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["bodyweight"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain"],
        "instructions": "Slide down a wall until knees are bent to a comfortable angle and hold the position. Keep your low back supported against the wall.",
        "category": "strength",
    },
    {
        "name": "Machine Chest Press",
        "muscle_groups": ["chest", "triceps", "front_delts"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["shoulder_pain"],
        "instructions": "Press the handles forward without shrugging the shoulders. Return with control until elbows reach a comfortable depth.",
        "category": "strength",
    },
    {
        "name": "Machine Seated Row",
        "muscle_groups": ["mid_back", "lats", "biceps"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_pain"],
        "instructions": "Row the handles toward your torso while keeping the chest supported or upright. Pause briefly and release slowly.",
        "category": "strength",
    },
    {
        "name": "Barbell Bent-Over Row",
        "muscle_groups": ["lats", "mid_back", "biceps"],
        "equipment": ["barbell"],
        "difficulty": "intermediate",
        "contraindications": ["acute_lower_back_pain"],
        "instructions": "Hinge forward with a stable torso and row the bar toward the lower ribs. Lower the bar with control and avoid jerking.",
        "category": "strength",
    },
    {
        "name": "Hammer Curl",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_elbow_pain"],
        "instructions": "Curl the dumbbells with a neutral grip while keeping the elbows close to the torso. Lower slowly to full extension.",
        "category": "strength",
    },
    {
        "name": "Dumbbell Lateral Raise",
        "muscle_groups": ["shoulders", "lateral_deltoid"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_pain"],
        "instructions": "Raise the dumbbells out to the sides to shoulder level with a slight bend in the elbows. Lower slowly without swinging.",
        "category": "strength",
    },
    {
        "name": "Overhead Tricep Extension",
        "muscle_groups": ["triceps"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_elbow_pain", "shoulder_pain"],
        "instructions": "Lower one dumbbell behind the head with elbows pointed upward, then extend the elbows to lockout. Keep the ribs down and upper arms stable.",
        "category": "strength",
    },
    {
        "name": "Cable Tricep Pushdown",
        "muscle_groups": ["triceps"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["acute_elbow_pain"],
        "instructions": "Press the rope or bar down by extending the elbows without swinging the shoulders. Return slowly to keep tension on the triceps.",
        "category": "strength",
    },
    {
        "name": "Face Pull",
        "muscle_groups": ["rear_delts", "upper_back", "rotator_cuff"],
        "equipment": ["cable_machine"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_inflammation"],
        "instructions": "Pull the rope toward the face with elbows high and wide. Squeeze the upper back, then return under control.",
        "category": "strength",
    },
    {
        "name": "Leg Extension",
        "muscle_groups": ["quadriceps"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain"],
        "instructions": "Extend the knees until the legs are straight without snapping into lockout. Lower the pad slowly to maintain control.",
        "category": "strength",
    },
    {
        "name": "Leg Curl",
        "muscle_groups": ["hamstrings"],
        "equipment": ["machines"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain"],
        "instructions": "Curl the pad toward the glutes while keeping the hips stable. Pause briefly and lower with control.",
        "category": "strength",
    },
    {
        "name": "Bulgarian Split Squat",
        "muscle_groups": ["quadriceps", "glutes", "adductors"],
        "equipment": ["bodyweight", "dumbbells", "bench"],
        "difficulty": "intermediate",
        "contraindications": ["acute_knee_pain", "ankle_instability"],
        "instructions": "Place the back foot on a bench and lower into a split squat with control. Drive through the front foot to stand without collapsing the torso.",
        "category": "strength",
    },
    {
        "name": "Calf Raise",
        "muscle_groups": ["calves"],
        "equipment": ["bodyweight", "machines", "dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_achilles_pain"],
        "instructions": "Rise onto the balls of the feet as high as possible, pause briefly, then lower slowly below the starting position if comfortable.",
        "category": "strength",
    },
    {
        "name": "Reverse Lunge",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["bodyweight", "dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_knee_pain", "balance_impairment"],
        "instructions": "Step backward into a lunge and lower until the front leg reaches a controlled depth. Push through the front foot to return to standing.",
        "category": "strength",
    },
    {
        "name": "Rear Delt Fly",
        "muscle_groups": ["rear_delts", "upper_back"],
        "equipment": ["dumbbells"],
        "difficulty": "beginner",
        "contraindications": ["acute_shoulder_pain"],
        "instructions": "Hinge slightly at the hips and open the arms wide while squeezing the upper back. Lower the dumbbells slowly and avoid shrugging.",
        "category": "strength",
    },
]


async def seed_exercises() -> None:
    """Insert baseline exercises unless collection is already populated."""

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    collection = client[settings.mongodb_db_name]["exercises"]

    inserted_count = 0
    skipped_count = 0

    try:
        existing_count = await collection.estimated_document_count()
        existing_names = {
            doc["name"]
            async for doc in collection.find({}, {"_id": 0, "name": 1})
            if doc.get("name")
        }
        new_exercises = [
            exercise for exercise in EXERCISES if exercise["name"] not in existing_names
        ]

        if not new_exercises:
            skipped_count = len(EXERCISES)
            print(
                f"Skipped insertion: exercises collection already contains {existing_count} document(s)."
            )
            print(f"Inserted: {inserted_count}")
            print(f"Skipped: {skipped_count}")
            return

        result = await collection.insert_many(new_exercises, ordered=True)
        inserted_count = len(result.inserted_ids)
        skipped_count = max(len(EXERCISES) - inserted_count, 0)

        print(f"Inserted: {inserted_count}")
        print(f"Skipped: {skipped_count}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_exercises())
