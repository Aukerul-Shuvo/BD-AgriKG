# NORA runs re-scored under the corrected grader

Graph: the v1 snapshot as evaluated (gold reproduced 460/460). OLD = grader of the submitted paper, NEW = eval/grading.py (booleans strict, collect() unpacked).

| run | n | stored ok ≠ OLD | strict OLD | strict NEW | lenient OLD | lenient NEW | items changed |
|---|---|---|---|---|---|---|---|
| bedrock_us.anthropic.claude-haiku-4-5-20251001-v1_0_bn | 460 | 0 | 218 | 218 | 234 | 234 | none |
| bedrock_us.anthropic.claude-haiku-4-5-20251001-v1_0_en | 460 | 0 | 236 | 236 | 243 | 243 | none |
| bedrock_us.anthropic.claude-opus-5_bn | 460 | 0 | 418 | 418 | 457 | 457 | none |
| bedrock_us.anthropic.claude-opus-5_en | 460 | 0 | 438 | 438 | 457 | 457 | none |
| bedrock_us.anthropic.claude-sonnet-5_bn | 460 | 0 | 388 | 388 | 448 | 448 | none |
| bedrock_us.anthropic.claude-sonnet-5_en | 460 | 0 | 436 | 436 | 458 | 458 | none |
| bedrock_us.deepseek.r1-v1_0_bn | 460 | 0 | 336 | 339 | 353 | 356 | upazila_soils-002:+, pests_of_top_crop-007:+, pests_of_top_crop-017:+ |
| bedrock_us.deepseek.r1-v1_0_en | 460 | 2 | 368 | 370 | 373 | 375 | upazila_soils-001:+, upazila_soils-005:+ |
| bedrock_us.meta.llama3-1-8b-instruct-v1_0_bn | 460 | 0 | 37 | 37 | 37 | 37 | none |
| bedrock_us.meta.llama3-1-8b-instruct-v1_0_en | 460 | 3 | 44 | 44 | 44 | 44 | none |
| bedrock_us.meta.llama3-3-70b-instruct-v1_0_bn | 460 | 0 | 133 | 133 | 133 | 133 | none |
| bedrock_us.meta.llama3-3-70b-instruct-v1_0_en | 460 | 1 | 158 | 158 | 158 | 158 | none |
| bedrock_us.mistral.pixtral-large-2502-v1_0_bn | 460 | 0 | 297 | 297 | 301 | 301 | none |
| bedrock_us.mistral.pixtral-large-2502-v1_0_en | 460 | 0 | 360 | 360 | 368 | 368 | none |
| rerun_bedrock_us.anthropic.claude-haiku-4-5-20251001-v1_0_en | 460 | 0 | 234 | 234 | 237 | 237 | none |
| retry_us.anthropic.claude-haiku-4-5-20251001-v1_0_bn | 81 | 0 | 46 | 46 | 55 | 55 | none |
| retry_us.anthropic.claude-haiku-4-5-20251001-v1_0_en | 72 | 0 | 42 | 42 | 46 | 46 | none |
| retry_us.anthropic.claude-opus-5_bn | 0 | 0 | 0 | 0 | 0 | 0 | none |
| retry_us.anthropic.claude-opus-5_en | 1 | 0 | 1 | 1 | 1 | 1 | none |
| retry_us.anthropic.claude-sonnet-5_bn | 0 | 0 | 0 | 0 | 0 | 0 | none |
| retry_us.anthropic.claude-sonnet-5_en | 0 | 0 | 0 | 0 | 0 | 0 | none |
| retry_us.deepseek.r1-v1_0_bn | 71 | 0 | 52 | 52 | 55 | 55 | none |
| retry_us.deepseek.r1-v1_0_en | 58 | 0 | 35 | 37 | 38 | 40 | pests_of_top_crop-008:+, pests_of_top_crop-015:+ |
| retry_us.meta.llama3-1-8b-instruct-v1_0_bn | 278 | 0 | 0 | 0 | 0 | 0 | none |
| retry_us.meta.llama3-1-8b-instruct-v1_0_en | 304 | 0 | 1 | 1 | 1 | 1 | none |
| retry_us.meta.llama3-3-70b-instruct-v1_0_bn | 177 | 0 | 2 | 2 | 2 | 2 | none |
| retry_us.meta.llama3-3-70b-instruct-v1_0_en | 191 | 0 | 11 | 11 | 12 | 12 | none |
| retry_us.mistral.pixtral-large-2502-v1_0_bn | 114 | 0 | 49 | 49 | 49 | 49 | none |
| retry_us.mistral.pixtral-large-2502-v1_0_en | 74 | 0 | 34 | 34 | 34 | 34 | none |
