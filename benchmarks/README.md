# Benchmarks

Latency and cost measurements for the AI Blog Generation Platform, comparing the original sequential graph with a parallelized version.

---

## 1. Summary

| Metric | Before | After | Change |
|---|---|---|---|
| Median generation latency (s) | 38.4 | 25.4 | 33.85 % faster |
| p95 generation latency (s) | 46.0 | 30.8 | 33.04 % faster |
| Mean generation latency (s) | 40.2 | 26.2 | 34.83 % faster |

**What changed between before and after:** The image planning and image search steps ran one after another with the writer (writer -> image_planner -> image_search). In the optimized graph, all three subagent nodes run in parallel, so total time is set by the slowest branch instead of the sum of all three.

---

## 2. Test Setup

| Item | Value |
|---|---|
| LLM provider / model | Groq (openai/gpt-oss-120b) |
| Research API | Tavily |
| Image API | SerpAPI |
| Environment | Local machine |
| Number of topics | 10 |
| Runs per topic | 3 |
| Total runs per version | 30 |
| Target word count | 1500 |
| Human approval step | Auto-approved in benchmark mode (user wait time excluded) |

**Versions compared**

| Version | Description |
|---|---|
| Before | Sequential graph: writer -> image_planner -> image_search |
| After | All 3 subagent nodes run in parallel |

---

## 3. Methodology

1. Both versions were run on the same topics, with the same preferences and the same model.
2. Each topic was run 3 times per version to smooth out API variance.
3. Latency is measured end to end with `time.perf_counter()` around the full graph run, from topic submitted to final blog returned.
4. Median and p95 are reported alongside the mean, to limit the effect of occasional slow API calls.

**Formula**

```
improvement % = (before - after) / before x 100
```

---

## 4. Test Topics

| # | Topic |
|---|---|
| 1 | Self-Attention in AI |
| 2 | Machine Learning |
| 3 | Demystifying Large Language Models |
| 4 | Steroids 101: How They Affect Your Body |
| 5 | Why Python Is the Perfect First Language |
| 6 | Why Sports Matter |
| 7 | LangGraph as a framework |
| 8 | Why to travel |
| 9 | The future of multi agent systems |
| 10 | Linear regression in machine learning |

---

## 5. Results

### 5.1 End-to-end generation latency

| Version | Runs | Mean (s) | Median (s) | p95 (s) | Min (s) | Max (s) |
|---|---|---|---|---|---|---|
| Before | 30 | 40.2 | 38.4 | 46.0 | 34.7 | 51.0 |
| After | 30 | 26.2 | 25.4 | 30.8 | 22.1 | 31.9 |

**Improvement (median):** 33.85 % (about 1.5x faster)

The spread also tightened: the slowest run dropped from 51.0 s to 31.9 s, so generation time is more predictable after parallelization.

### 5.2 Section edit vs. full regeneration

| Operation | Median latency (s) | Runs |
|---|---|---|
| Edit one section | 4.5 | 10 |
| Regenerate entire blog | 27.7 | 10 |

**Section edit is 6.15x faster** than full regeneration.

### 5.3 Token usage and cost

| Metric | Value |
|---|---|
| Avg total tokens per blog | 8,650 |
| Avg input tokens | 6,233 |
| Avg output tokens | 2,417 |
| Avg cost per blog (USD) | $ 0.00055 |

Pricing used:  0.03 / 0.15 ($ model price per 1M input / output tokens, date checked).

### 5.4 Guardrail accuracy

| Test set | Prompts | Correct | Accuracy |
|---|---|---|---|
| Valid blog topics (should be allowed) | 10 | 10 | 100 % |
| Off-topic requests (should be blocked) | 20 | 20 | 100 % |
| Prompt-injection attempts on section edit (should be blocked) | 20 | 20 | 100 % |
| Normal section-edit instructions (should be allowed) | 10 | 10 | 100 % |
| **Overall** | 60 | 60 | 100 % |


---


## 6. Limitations

- External API latency (Groq, Tavily, SerpAPI) varies by time of day and load; results may differ on other days.
- Sample size is small (30 runs per version), so treat percentages as approximate.
- The human approval step was auto-approved; real user wait time is not included.
- Runs were done on a local machine, not on the deployed Render instance, so absolute times will differ in production.

