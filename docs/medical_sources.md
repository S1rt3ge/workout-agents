# Medical Constraint Sources

This table documents the authoritative provenance behind the `medical_constraints`
knowledge base. The system uses these records as a structured training-safety layer,
not as a diagnosis or treatment engine.

## Evidence Rules

- `guideline_based`: government or professional clinical guideline used directly for conservative training modification.
- `consensus_based`: expert consensus or best-practice source used only when a narrower official exercise-modification guideline is not available.
- Condition names may be widened into symptom clusters when official sources support conservative loading rules but do not justify diagnosis-specific exercise prescriptions.

## Source Map

| condition_id | canonical_name | issuing_body | source_title | source_type | year | why_used |
|---|---|---|---|---|---:|---|
| `shoulder_pain_overhead_restriction` | Shoulder pain with overhead loading restriction | Australian Commission on Safety and Quality in Health Care | Shoulder Pain Clinical Care Standard | government_guideline | 2023 | Supports conservative avoidance of symptom-aggravating shoulder loading. |
| `shoulder_pain_overhead_restriction` | Shoulder pain with overhead loading restriction | JOSPT/APTA | Rotator Cuff Tendinopathy Diagnosis, Non-surgical Medical Care and Rehabilitation: A Clinical Practice Guideline | professional_guideline | 2025 | Supports symptom-guided return to upper-body loading. |
| `lower_back_pain` | Lower back pain | WHO | WHO Guideline for Non-surgical Management of Chronic Primary Low Back Pain | government_guideline | 2023 | Supports conservative exercise-based management and symptom-guided loading. |
| `lower_back_pain` | Lower back pain | NICE | Low back pain and sciatica in over 16s: assessment and management | government_guideline | 2020 | Supports avoiding aggravating loading and maintaining conservative movement exposure. |
| `anterior_knee_pain_cluster` | Anterior knee pain or patellofemoral pain cluster | BJSM expert panel | Best Practice Guide to Conservative Management of Patellofemoral Pain | consensus_statement | 2024 | Supports conservative modification of deep knee flexion and impact loading. |
| `ankle_instability` | Ankle instability | JOSPT/APTA | Clinical Guidelines for Lateral Ankle Sprain and Chronic Ankle Instability | professional_guideline | 2021 | Supports balance-focused loading and caution with unstable high-impact tasks. |
| `hamstring_strain` | Hamstring strain | BJSM expert panel | BJSM Hamstring Injury Clinical and Return-to-Load Consensus | consensus_statement | 2023 | Supports caution around sprinting and ballistic hinging during symptomatic phases. |
| `elbow_tendinopathy` | Elbow tendinopathy | BESS | BESS Consensus for Lateral Elbow Tendinopathy | consensus_statement | 2022 | Supports conservative grip-load reduction rather than diagnosis-specific programming. |
| `hypertension` | Hypertension | ACC/AHA | 2017 ACC/AHA Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults | professional_guideline | 2018 | Supports blood-pressure-aware exercise prescription and caution with high-strain efforts. |
| `hypertension` | Hypertension | ACSM | ACSM Guidelines for Exercise Testing and Prescription | professional_guideline | 2021 | Supports submaximal resistance/aerobic dosing and steady breathing. |
| `obesity_deconditioning` | Obesity or deconditioning | WHO | Obesity and overweight guidance | government_guideline | 2024 | Supports lower-impact and progressive exercise entry. |
| `obesity_deconditioning` | Obesity or deconditioning | WHO | WHO Guidelines on Physical Activity and Sedentary Behaviour | government_guideline | 2020 | Supports graded physical activity progression for deconditioned adults. |
| `obesity_deconditioning` | Obesity or deconditioning | ACSM | ACSM Guidelines for Exercise Testing and Prescription | professional_guideline | 2021 | Supports conservative exercise dosing and progression. |
| `postpartum_early_phase` | Postpartum early phase | ACOG | Physical Activity and Exercise During Pregnancy and the Postpartum Period | professional_guideline | 2020 | Supports conservative postpartum return-to-exercise loading. |
| `hernia_breath_holding_restriction` | Hernia risk or breath-holding restriction | HerniaSurge | International Guidelines for Groin Hernia Management | professional_guideline | 2018 | Supports caution with high-strain loading when abdominal-pressure management is needed. |
| `hernia_breath_holding_restriction` | Hernia risk or breath-holding restriction | ACSM | ACSM Guidelines for Exercise Testing and Prescription | professional_guideline | 2021 | Supports steady breathing and submaximal loading rules. |
| `gi_reflux_restriction` | GI reflux-related training restriction | American Gastroenterological Association | AGA Clinical Practice Update on the Personalized Approach to the Evaluation and Management of GERD | professional_guideline | 2022 | Supports symptom-trigger avoidance for body position and exertion timing. |
| `gi_ibs_symptom_flare` | GI symptom flare requiring lower-intensity training | American College of Gastroenterology | ACG Clinical Guideline: Management of Irritable Bowel Syndrome | professional_guideline | 2021 | Supports symptom-aware activity reduction during GI flare states. |
| `hip_impingement_symptom_cluster` | Hip pain with flexion intolerance or femoroacetabular impingement symptom cluster | Warwick Agreement group | The Warwick Agreement on Femoroacetabular Impingement Syndrome | consensus_statement | 2016 | Supports conservative modification of deep hip flexion, not narrow treatment claims. |
| `neck_pain` | Neck pain | JOSPT/APTA | Neck Pain Clinical Practice Guideline Revision | professional_guideline | 2017 | Supports cautious modification of cervical loading and overhead strain. |

## Academic Framing

Recommended wording for the thesis:

> The medical constraint layer is a manually curated, structured knowledge base derived from authoritative clinical guidelines and professional society guidance. The system uses this layer for conservative training adaptation and exercise exclusion logic, while avoiding diagnosis generation or treatment recommendations.

## Current Limits

- The catalog is intentionally conservative and incomplete.
- Some sports-medicine subdomains do not have a single official diagnosis-specific exercise guideline; in those cases the system stores a broader symptom or loading-intolerance cluster.
- Consensus-based records should be presented as lower-authority than guideline-based records.
