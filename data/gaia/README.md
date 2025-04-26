---
language:
- en
pretty_name: General AI Assistants Benchmark
extra_gated_prompt: "To avoid contamination and data leakage, you agree to not reshare this dataset outside of a gated or private repository on the HF hub."
extra_gated_fields:
  I agree to not reshare the GAIA submissions set according to the above conditions: checkbox
---
# GAIA dataset

GAIA is a benchmark which aims at evaluating next-generation LLMs (LLMs with augmented capabilities due to added tooling, efficient prompting, access to search, etc).

We added gating to prevent bots from scraping the dataset. Please do not reshare the validation or test set in a crawlable format.

## Data and leaderboard
GAIA is made of more than 450 non-trivial question with an unambiguous answer, requiring different levels of tooling and autonomy to solve. It is therefore divided in 3 levels, where level 1 should be breakable by very good LLMs, and level 3 indicate a strong jump in model capabilities. Each level is divided into a fully public dev set for validation, and a test set with private answers and metadata.

GAIA leaderboard can be found in this space (https://huggingface.co/spaces/gaia-benchmark/leaderboard).

Questions are contained in metadata.jsonl. Some questions come with an additional file, that can be found in the same folder and whose id is given in the field file_name.

More details in [the paper](https://arxiv.org/abs/2311.12983) for now and soon here as well.