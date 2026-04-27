"""Seed script for populating the medical_constraints collection."""

# ruff: noqa: E402, E501

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workout_agent.core.config import get_settings


def _normalize_term(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _with_search_terms(document: dict[str, Any]) -> dict[str, Any]:
    aliases = document.get("aliases", [])
    canonical_name = document.get("canonical_name", "")
    search_terms: list[str] = []
    for term in [canonical_name, *aliases, document.get("condition_id", "")]:
        normalized = _normalize_term(term)
        if normalized and normalized not in search_terms:
            search_terms.append(normalized)

    payload = dict(document)
    payload["search_terms"] = search_terms
    return payload


def _source(
    *,
    title: str,
    url: str,
    year: int,
    issuing_body: str,
    source_type: str,
    recommendation_strength: str,
    clinical_scope_note: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "url": url,
        "year": year,
        "issuing_body": issuing_body,
        "source_type": source_type,
        "recommendation_strength": recommendation_strength,
        "clinical_scope_note": clinical_scope_note,
    }


WHO_LBP = _source(
    title="WHO Guideline for Non-surgical Management of Chronic Primary Low Back Pain",
    url="https://www.who.int/publications/i/item/9789240081789",
    year=2023,
    issuing_body="WHO",
    source_type="government_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports conservative exercise modification and symptom-guided loading for low back pain.",
)

NICE_LBP = _source(
    title="Low back pain and sciatica in over 16s: assessment and management",
    url="https://www.nice.org.uk/guidance/ng59",
    year=2020,
    issuing_body="NICE",
    source_type="government_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports avoidance of aggravating loading and use of conservative exercise-based management.",
)

ACC_AHA_HTN = _source(
    title="2017 ACC/AHA Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults",
    url="https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065",
    year=2018,
    issuing_body="ACC/AHA",
    source_type="professional_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports blood-pressure-aware exercise prescription and caution with high-strain efforts.",
)

ACSM_EXERCISE = _source(
    title="ACSM Guidelines for Exercise Testing and Prescription",
    url="https://acsm.org",
    year=2021,
    issuing_body="ACSM",
    source_type="professional_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports submaximal aerobic and resistance training progression and breathing safety rules.",
)

ACOG_POSTPARTUM = _source(
    title="Physical Activity and Exercise During Pregnancy and the Postpartum Period",
    url="https://www.acog.org/clinical/clinical-guidance/committee-opinion/articles/2020/04/physical-activity-and-exercise-during-pregnancy-and-the-postpartum-period",
    year=2020,
    issuing_body="ACOG",
    source_type="professional_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports conservative postpartum return-to-exercise progressions and pelvic-floor aware loading.",
)

WHO_OBESITY = _source(
    title="Obesity and overweight guidance",
    url="https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight",
    year=2024,
    issuing_body="WHO",
    source_type="government_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports lower-impact exercise selection and gradual volume progression for obesity/deconditioning.",
)

WHO_ACTIVITY = _source(
    title="WHO Guidelines on Physical Activity and Sedentary Behaviour",
    url="https://www.who.int/publications/i/item/9789240015128",
    year=2020,
    issuing_body="WHO",
    source_type="government_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports graded physical activity and lower-barrier movement exposure in deconditioned adults.",
)

ACG_IBS = _source(
    title="ACG Clinical Guideline: Management of Irritable Bowel Syndrome",
    url="https://gi.org/guideline/management-of-irritable-bowel-syndrome/",
    year=2021,
    issuing_body="American College of Gastroenterology",
    source_type="professional_guideline",
    recommendation_strength="moderate",
    clinical_scope_note="Supports symptom-aware activity modification during GI symptom flares, not medical treatment claims.",
)

AGA_GERD = _source(
    title="AGA Clinical Practice Update on the Personalized Approach to the Evaluation and Management of GERD",
    url="https://www.gastrojournal.org",
    year=2022,
    issuing_body="American Gastroenterological Association",
    source_type="professional_guideline",
    recommendation_strength="moderate",
    clinical_scope_note="Supports conservative avoidance of symptom-provoking body positions and post-meal high-intensity training.",
)

SHOULDER_STANDARD = _source(
    title="Shoulder Pain Clinical Care Standard",
    url="https://www.safetyandquality.gov.au/standards/clinical-care-standards/shoulder-pain-clinical-care-standard",
    year=2023,
    issuing_body="Australian Commission on Safety and Quality in Health Care",
    source_type="government_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports conservative shoulder pain management and avoidance of symptom-aggravating loading.",
)

ROTATOR_CUFF_CPG = _source(
    title="Rotator Cuff Tendinopathy Diagnosis, Non-surgical Medical Care and Rehabilitation: A Clinical Practice Guideline",
    url="https://www.jospt.org/doi/10.2519/jospt.2025.0301",
    year=2025,
    issuing_body="JOSPT/APTA",
    source_type="professional_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports conservative shoulder loading modification and symptom-guided return to upper-body work.",
)

PFP_BEST_PRACTICE = _source(
    title="Best Practice Guide to Conservative Management of Patellofemoral Pain",
    url="https://bjsm.bmj.com/content/58/24/1486",
    year=2024,
    issuing_body="BJSM expert panel",
    source_type="consensus_statement",
    recommendation_strength="moderate",
    clinical_scope_note="Supports conservative modification of deep knee flexion, impact, and exercise loading for anterior knee pain clusters.",
)

ANKLE_CPG = _source(
    title="Clinical Guidelines for Lateral Ankle Sprain and Chronic Ankle Instability",
    url="https://www.jospt.org/doi/10.2519/jospt.2021.0302",
    year=2021,
    issuing_body="JOSPT/APTA",
    source_type="professional_guideline",
    recommendation_strength="high",
    clinical_scope_note="Supports balance-focused rehabilitation and cautious modification of unstable high-impact tasks.",
)

NECK_CPG = _source(
    title="Neck Pain Clinical Practice Guideline Revision",
    url="https://www.jospt.org/doi/10.2519/jospt.2017.0302",
    year=2017,
    issuing_body="JOSPT/APTA",
    source_type="professional_guideline",
    recommendation_strength="moderate",
    clinical_scope_note="Supports conservative loading modification for painful cervical positions and high-tension upper-body tasks.",
)

HERNIA_GUIDELINE = _source(
    title="International Guidelines for Groin Hernia Management",
    url="https://pubmed.ncbi.nlm.nih.gov/29330835/",
    year=2018,
    issuing_body="HerniaSurge",
    source_type="professional_guideline",
    recommendation_strength="moderate",
    clinical_scope_note="Supports conservative avoidance of high-strain loading when hernia symptoms or risk require caution.",
)

HIP_FAI = _source(
    title="The Warwick Agreement on Femoroacetabular Impingement Syndrome",
    url="https://bjsm.bmj.com/content/50/19/1169",
    year=2016,
    issuing_body="Warwick Agreement group",
    source_type="consensus_statement",
    recommendation_strength="moderate",
    clinical_scope_note="Supports symptom-limited modification of deep hip flexion rather than diagnosis-specific treatment claims.",
)

HAMSTRING_CONSENSUS = _source(
    title="BJSM Hamstring Injury Clinical and Return-to-Load Consensus",
    url="https://bjsm.bmj.com/content/57/9/548",
    year=2023,
    issuing_body="BJSM expert panel",
    source_type="consensus_statement",
    recommendation_strength="moderate",
    clinical_scope_note="Supports cautious progression away from ballistic hinging and sprinting during symptomatic hamstring phases.",
)

ELBOW_CONSENSUS = _source(
    title="BESS Consensus for Lateral Elbow Tendinopathy",
    url="https://bess.ac.uk",
    year=2022,
    issuing_body="BESS",
    source_type="consensus_statement",
    recommendation_strength="moderate",
    clinical_scope_note="Supports reducing gripping load and upper-limb strain rather than prescribing treatment.",
)


MEDICAL_CONSTRAINTS: list[dict[str, Any]] = [
    {
        "condition_id": "shoulder_pain_overhead_restriction",
        "canonical_name": "Shoulder pain with overhead loading restriction",
        "aliases": [
            "shoulder strain",
            "strained shoulder",
            "shoulder impingement",
            "subacromial pain",
            "rotator cuff irritation",
            "rotator cuff pain",
            "painful overhead reaching",
            "shoulder hurts when pressing",
        ],
        "condition_type": "pain_condition",
        "affected_body_parts": ["shoulder", "rotator cuff"],
        "movement_restrictions": [
            "loaded overhead pressing",
            "loaded shoulder abduction",
            "explosive upper body pushing",
        ],
        "safe_alternatives": [
            "pain-free horizontal pulling",
            "light rotator cuff stability work",
            "lower body training",
        ],
        "contraindicated_exercise_keywords": [
            "overhead press",
            "arnold press",
            "lateral raise",
            "push press",
            "upright row",
        ],
        "training_notes": "This record is framed as a conservative shoulder pain modification profile, not a diagnosis-specific treatment protocol.",
        "risk_level": "moderate",
        "evidence_level": "guideline_based",
        "sources": [SHOULDER_STANDARD, ROTATOR_CUFF_CPG],
    },
    {
        "condition_id": "lower_back_pain",
        "canonical_name": "Lower back pain",
        "aliases": ["low back pain", "back pain", "lumbar pain", "sore lower back"],
        "condition_type": "pain_condition",
        "affected_body_parts": ["lower back", "lumbar spine"],
        "movement_restrictions": [
            "high-load spinal flexion",
            "high-load hip hinging",
            "ballistic trunk loading",
        ],
        "safe_alternatives": [
            "supported lower-body training",
            "pain-free walking or cycling",
            "core stability work with neutral spine",
        ],
        "contraindicated_exercise_keywords": [
            "deadlift",
            "good morning",
            "kettlebell swing",
            "rowing ergometer",
        ],
        "training_notes": "This profile supports conservative symptom-guided loading rather than structural diagnosis claims.",
        "risk_level": "high",
        "evidence_level": "guideline_based",
        "sources": [WHO_LBP, NICE_LBP],
    },
    {
        "condition_id": "anterior_knee_pain_cluster",
        "canonical_name": "Anterior knee pain or patellofemoral pain cluster",
        "aliases": [
            "knee pain",
            "sore knee",
            "left knee pain",
            "right knee pain",
            "runner's knee",
            "patellofemoral pain",
            "front of knee pain",
        ],
        "condition_type": "pain_condition",
        "affected_body_parts": ["knee", "patellofemoral joint"],
        "movement_restrictions": [
            "deep loaded knee flexion",
            "repetitive jumping",
            "high-volume stair or step-down loading",
        ],
        "safe_alternatives": [
            "partial-range squat variations",
            "glute-focused strengthening",
            "lower-impact cardio",
        ],
        "contraindicated_exercise_keywords": [
            "walking lunge",
            "jump rope",
            "box jump",
            "deep squat",
            "burpee",
        ],
        "training_notes": "This is an anterior knee pain training-modification cluster using conservative loading guidance.",
        "risk_level": "moderate",
        "evidence_level": "consensus_based",
        "sources": [PFP_BEST_PRACTICE],
    },
    {
        "condition_id": "ankle_instability",
        "canonical_name": "Ankle instability",
        "aliases": ["weak ankle", "unstable ankle", "recurrent ankle sprain"],
        "condition_type": "injury",
        "affected_body_parts": ["ankle"],
        "movement_restrictions": [
            "unstable single-leg landing",
            "high-impact plyometrics",
            "rapid cutting and pivoting",
        ],
        "safe_alternatives": [
            "supported single-leg balance work",
            "machine-based lower-body exercises",
            "cycling or rowing if tolerated",
        ],
        "contraindicated_exercise_keywords": ["jump rope", "box jump", "walking lunge", "burpee"],
        "training_notes": "This profile follows instability-focused return-to-load caution and favors stable surfaces and slower tempo.",
        "risk_level": "moderate",
        "evidence_level": "guideline_based",
        "sources": [ANKLE_CPG],
    },
    {
        "condition_id": "hamstring_strain",
        "canonical_name": "Hamstring strain",
        "aliases": ["pulled hamstring", "strained hamstring", "hamstring pain"],
        "condition_type": "injury",
        "affected_body_parts": ["hamstrings", "posterior thigh"],
        "movement_restrictions": [
            "ballistic hip hinging",
            "maximal sprinting",
            "long-length hamstring loading in pain",
        ],
        "safe_alternatives": [
            "short-range glute bridge variations",
            "light cycling",
            "pain-limited lower-body isometrics",
        ],
        "contraindicated_exercise_keywords": [
            "romanian deadlift",
            "kettlebell swing",
            "standing hamstring stretch",
            "sprint",
        ],
        "training_notes": "This record is conservative and symptom-based because evidence is stronger for return-to-load principles than for fixed exercise bans.",
        "risk_level": "high",
        "evidence_level": "consensus_based",
        "sources": [HAMSTRING_CONSENSUS],
    },
    {
        "condition_id": "elbow_tendinopathy",
        "canonical_name": "Elbow tendinopathy",
        "aliases": ["tennis elbow", "golfer's elbow", "elbow tendon pain"],
        "condition_type": "pain_condition",
        "affected_body_parts": ["elbow", "forearm"],
        "movement_restrictions": [
            "high-volume gripping",
            "maximal pulling",
            "rapid loaded elbow flexion-extension",
        ],
        "safe_alternatives": [
            "reduced-load cable pulling",
            "lower-body training",
            "pain-guided isometric forearm work",
        ],
        "contraindicated_exercise_keywords": ["pull-up", "chin-up", "heavy curl", "farmer carry"],
        "training_notes": "This record is a conservative training-modification profile based on professional consensus, not a definitive treatment recommendation.",
        "risk_level": "moderate",
        "evidence_level": "consensus_based",
        "sources": [ELBOW_CONSENSUS],
    },
    {
        "condition_id": "hypertension",
        "canonical_name": "Hypertension",
        "aliases": ["high blood pressure", "elevated blood pressure"],
        "condition_type": "chronic_condition",
        "affected_body_parts": ["cardiovascular system"],
        "movement_restrictions": [
            "breath-holding under heavy load",
            "all-out conditioning intervals",
            "maximal strength efforts",
        ],
        "safe_alternatives": [
            "moderate-intensity aerobic training",
            "submaximal resistance training with steady breathing",
            "circuit training with controlled effort",
        ],
        "contraindicated_exercise_keywords": ["burpee", "max deadlift", "max squat", "heavy carry"],
        "training_notes": "Use submaximal loading and coached breathing; this rule is intended for safe exercise prescription, not disease management.",
        "risk_level": "high",
        "evidence_level": "guideline_based",
        "sources": [ACC_AHA_HTN, ACSM_EXERCISE],
    },
    {
        "condition_id": "obesity_deconditioning",
        "canonical_name": "Obesity or deconditioning",
        "aliases": ["deconditioned", "out of shape", "obesity", "sedentary beginner"],
        "condition_type": "conditioning_status",
        "affected_body_parts": ["cardiorespiratory system", "weight-bearing joints"],
        "movement_restrictions": [
            "high-impact plyometrics",
            "advanced metabolic circuits",
            "abrupt volume spikes",
        ],
        "safe_alternatives": [
            "low-impact cardio",
            "machine or supported resistance training",
            "shorter sessions with gradual progression",
        ],
        "contraindicated_exercise_keywords": ["burpee", "jump rope", "box jump", "advanced hiit"],
        "training_notes": "This profile targets conservative entry-level loading and adherence, not obesity treatment per se.",
        "risk_level": "moderate",
        "evidence_level": "guideline_based",
        "sources": [WHO_OBESITY, WHO_ACTIVITY, ACSM_EXERCISE],
    },
    {
        "condition_id": "postpartum_early_phase",
        "canonical_name": "Postpartum early phase",
        "aliases": ["early postpartum", "recently postpartum", "just gave birth"],
        "condition_type": "special_population",
        "affected_body_parts": ["abdominal wall", "pelvic floor"],
        "movement_restrictions": [
            "high-pressure abdominal bracing",
            "high-impact jumping",
            "early return to intense loaded core work",
        ],
        "safe_alternatives": [
            "walking",
            "breathing-based deep core work",
            "light full-body resistance training within medical clearance",
        ],
        "contraindicated_exercise_keywords": ["plank", "burpee", "sit-up", "double under"],
        "training_notes": "This profile reflects conservative postpartum exercise modification and should remain subordinate to clinical clearance.",
        "risk_level": "high",
        "evidence_level": "guideline_based",
        "sources": [ACOG_POSTPARTUM],
    },
    {
        "condition_id": "hernia_breath_holding_restriction",
        "canonical_name": "Hernia risk or breath-holding restriction",
        "aliases": ["hernia risk", "avoid valsalva", "cannot hold breath under load"],
        "condition_type": "restriction",
        "affected_body_parts": ["abdominal wall"],
        "movement_restrictions": [
            "heavy straining",
            "valsalva maneuver",
            "near-maximal compound lifting",
        ],
        "safe_alternatives": [
            "machine-based resistance work",
            "moderate loads with exhale on effort",
            "walking and lower-impact conditioning",
        ],
        "contraindicated_exercise_keywords": [
            "max deadlift",
            "max squat",
            "heavy carry",
            "farmer carry",
            "ab wheel",
            "plank",
        ],
        "training_notes": "This is a conservative abdominal-pressure management rule intended for exercise safety, not diagnosis confirmation.",
        "risk_level": "high",
        "evidence_level": "guideline_based",
        "sources": [HERNIA_GUIDELINE, ACSM_EXERCISE],
    },
    {
        "condition_id": "gi_reflux_restriction",
        "canonical_name": "GI reflux-related training restriction",
        "aliases": ["acid reflux", "gerd", "reflux during exercise"],
        "condition_type": "restriction",
        "affected_body_parts": ["upper gastrointestinal tract"],
        "movement_restrictions": [
            "high-impact exercise soon after meals",
            "prolonged prone pressure",
            "max-effort intervals when symptomatic",
        ],
        "safe_alternatives": [
            "upright moderate-intensity cardio",
            "resistance training with longer rest",
            "training further away from meals",
        ],
        "contraindicated_exercise_keywords": ["burpee", "mountain climber", "sit-up", "plank"],
        "training_notes": "This record is intentionally framed as a symptom-trigger avoidance rule, not a GERD treatment recommendation.",
        "risk_level": "low",
        "evidence_level": "guideline_based",
        "sources": [AGA_GERD],
    },
    {
        "condition_id": "gi_ibs_symptom_flare",
        "canonical_name": "GI symptom flare requiring lower-intensity training",
        "aliases": ["ibs flare", "stomach flare", "gi symptoms during training"],
        "condition_type": "restriction",
        "affected_body_parts": ["gastrointestinal system"],
        "movement_restrictions": [
            "vigorous interval training during symptom flare",
            "long sessions without breaks",
            "high-pressure abdominal work",
        ],
        "safe_alternatives": [
            "light walking",
            "short low-intensity sessions",
            "machine work with flexible rest periods",
        ],
        "contraindicated_exercise_keywords": [
            "burpee",
            "assault bike sprint",
            "ab wheel",
            "double under",
            "plank",
            "mountain climber",
        ],
        "training_notes": "This record is a temporary activity-modification profile for symptom flares and avoids making medical treatment claims.",
        "risk_level": "low",
        "evidence_level": "guideline_based",
        "sources": [ACG_IBS],
    },
    {
        "condition_id": "hip_impingement_symptom_cluster",
        "canonical_name": "Hip pain with flexion intolerance or femoroacetabular impingement symptom cluster",
        "aliases": ["fai", "femoroacetabular impingement", "hip impingement", "pinching hip pain"],
        "condition_type": "pain_condition",
        "affected_body_parts": ["hip", "anterior hip"],
        "movement_restrictions": [
            "deep loaded hip flexion",
            "aggressive end-range squatting",
            "explosive pivoting if painful",
        ],
        "safe_alternatives": [
            "box squat to tolerated depth",
            "hip hinge variations within tolerance",
            "cycling with seat adjusted for comfort",
        ],
        "contraindicated_exercise_keywords": ["deep squat", "walking lunge", "single-leg glute bridge", "high knee"],
        "training_notes": "This is a symptom-cluster record because source support is stronger for conservative modification than for narrow diagnosis-specific exercise bans.",
        "risk_level": "moderate",
        "evidence_level": "consensus_based",
        "sources": [HIP_FAI],
    },
    {
        "condition_id": "neck_pain",
        "canonical_name": "Neck pain",
        "aliases": ["sore neck", "cervical pain", "stiff neck"],
        "condition_type": "pain_condition",
        "affected_body_parts": ["neck", "cervical spine"],
        "movement_restrictions": [
            "heavy axial loading",
            "explosive overhead work",
            "high-tension shrugging",
        ],
        "safe_alternatives": [
            "supported machine work",
            "lower-body training",
            "light rowing with relaxed shoulder posture",
        ],
        "contraindicated_exercise_keywords": ["overhead press", "push press", "barbell back squat", "heavy shrug"],
        "training_notes": "This profile uses conservative cervical loading restrictions consistent with guideline-level neck pain management.",
        "risk_level": "moderate",
        "evidence_level": "guideline_based",
        "sources": [NECK_CPG],
    },
]


async def main() -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)

    inserted = 0
    updated = 0
    skipped = 0

    try:
        collection = client[settings.mongodb_db_name]["medical_constraints"]
        await collection.create_index("condition_id", unique=True)
        await collection.create_index("search_terms")

        for raw_document in MEDICAL_CONSTRAINTS:
            document = _with_search_terms(raw_document)
            existing = await collection.find_one(
                {"condition_id": document["condition_id"]},
                {"_id": 0},
            )

            if existing is None:
                await collection.insert_one(document)
                inserted += 1
                continue

            comparable_existing = dict(existing)
            if comparable_existing == document:
                skipped += 1
                continue

            await collection.update_one(
                {"condition_id": document["condition_id"]},
                {"$set": document},
            )
            updated += 1
    finally:
        client.close()

    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
