# Filename Signal Removal Impact Analysis

## Context

After removing filename token matching from the ranking algorithm (removed `_FILENAME_TOKEN_BOOST = 0.03` from `ranking_service.py`), live judged-query evaluation dropped significantly:

**Before filename removal:**
- Precision@10: 0.1000
- Recall@10: 0.9444
- MRR: 0.6214
- NDCG@10: 0.6695

**After filename removal (current):**
- Precision@10: 0.0700
- Recall@10: 0.5500
- MRR: 0.2499
- NDCG@10: 0.2939

**Delta:**
- Precision@10: -30% (0.1000 → 0.0700)
- Recall@10: -42% (0.9444 → 0.5500)
- MRR: -60% (0.6214 → 0.2499)
- NDCG@10: -56% (0.6695 → 0.2939)

## Current Per-Query Performance

### Strong Queries (MRR ≥ 0.5)

1. **q006 (office desk)**: MRR 1.0000, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:7` at rank 1 (correct)
   - Caption: "There are many people sitting around a conference table with laptops."
   - **Strong semantic match between query and caption**

2. **q007 (dog playing)**: MRR 1.0000, P@10 0.2000, R@10 0.5000
   - Retrieved: `scene:20` at rank 1 (correct)
   - Caption: dog-related scenes
   - **Strong semantic match**

3. **q009 (person sitting)**: MRR 1.0000, P@10 0.2000, R@10 1.0000
   - Retrieved: `media:8` at rank 1 (correct)
   - Caption: "There is a person sitting at a table with a laptop and cell phone."
   - **Strong semantic match**

4. **q014 (indoor room)**: MRR 0.5000, P@10 0.1000, R@10 0.5000
   - Retrieved: `media:7` at rank 2
   - **Moderate semantic match**

### Weak Queries (MRR < 0.5)

5. **q019 (building)**: MRR 0.3333, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:7` at rank 3
   - Target: office interior (weak "building" association)

6. **q003 (sunset beach)**: MRR 0.2500, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:6` at rank 4
   - Caption: "There is a dock sitting in the middle of a lake."
   - **Semantic mismatch: "sunset beach" vs "dock lake"**

7. **q001 (cat)**: MRR 0.2000, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:4` at rank 5
   - Caption: "There are two dogs that are sitting in the grass together."
   - **Caption drift: cat.jpg captioned as dogs**

8. **q016 (water)**: MRR 0.2000, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:6` at rank 5
   - Caption: "There is a dock sitting in the middle of a lake."
   - **Weak semantic match: "water" present but not prominent**

9. **q010 (city street)**: MRR 0.1667, P@10 0.1000, R@10 1.0000
   - Retrieved: `media:5` at rank 6
   - Caption: "Picture of a blue bmw car parked on the side of the road."
   - **Weak semantic match: "road" vs "city street"**

10. **q013 (tree)**: MRR 0.1250, P@10 0.1000, R@10 1.0000
    - Retrieved: `media:8` at rank 8
    - Caption: "There is a person sitting at a table with a laptop and cell phone."
    - **No semantic match for "tree"**

11. **q008 (mountain landscape)**: MRR 0.1111, P@10 0.1000, R@10 1.0000
    - Retrieved: `media:8` at rank 9
    - Caption: "There is a person sitting at a table with a laptop and cell phone."
    - **Caption drift: mountain.jpg captioned as indoor scene**

12. **q015 (person talking)**: MRR 0.1111, P@10 0.1000, R@10 1.0000
    - Retrieved: `media:9` at rank 9
    - Caption: "Image content unclear."
    - **Weak caption quality**

### Failed Queries (MRR = 0.0000)

13. **q002 (person walking)**: No relevant items in corpus (explicit negative)
14. **q004 (red car)**: No relevant items in corpus (explicit negative: car is blue)
15. **q005 (cooking)**: No relevant items in corpus (explicit negative)
16. **q011 (blue sky)**: Retrieved `media:8` at rank 11 (outside top-10)
    - Target: `media:8` (mountain.jpg)
    - **Caption drift prevents match**
17. **q012 (running)**: No relevant items in corpus (explicit negative)
18. **q017 (night scene)**: Retrieved `media:9` at rank 11 (outside top-10)
    - Target: `media:9` (dark screenshot)
    - **Weak caption: "Image content unclear."**
19. **q018 (eating)**: No relevant items in corpus (explicit negative)
20. **q020 (forest)**: No relevant items in corpus (explicit negative)

## Root Cause Analysis

### 1. Caption Drift (Primary Issue)

Several queries fail because the generated captions do not match the actual visual content:

- **q001 (cat)**: `cat.jpg` → "There are two dogs that are sitting in the grass together."
- **q008 (mountain landscape)**: `mountain.jpg` → "There is a person sitting at a table with a laptop and cell phone."
- **q011 (blue sky)**: `mountain.jpg` → same indoor caption

**Impact:** These queries previously benefited from filename token matching (`cat`, `mountain`) which compensated for caption drift. Without filename signal, they rely entirely on broken captions.

### 2. Weak Semantic Overlap

Some queries have weak semantic overlap between query terms and caption vocabulary:

- **q003 (sunset beach)**: "sunset beach" vs "dock sitting in the middle of a lake"
- **q010 (city street)**: "city street" vs "car parked on the side of the road"
- **q016 (water)**: "water" vs "dock sitting in the middle of a lake" (water implied but not explicit)

**Impact:** Filename tokens (`beach.jpg`, `car.jpg`) previously provided exact-match signal that boosted these results. Without it, the weaker semantic overlap from captions alone is insufficient.

### 3. Weak Caption Quality

Some captions are too generic or fallback to "Image content unclear.":

- **q015 (person talking)**: `media:9` → "Image content unclear."
- **q017 (night scene)**: `media:9` → "Image content unclear."

**Impact:** No semantic signal from caption; filename was the only signal.

## Filename Signal Dependency Pattern

Queries that likely depended on filename token matching:

1. **q001 (cat)**: filename `cat.jpg` provided exact match; caption says "dogs"
2. **q003 (sunset beach)**: filename `beach.jpg` provided exact match; caption says "dock lake"
3. **q008 (mountain landscape)**: filename `mountain.jpg` provided exact match; caption says "person at table"
4. **q010 (city street)**: filename `car.jpg` provided partial match; caption says "road"
5. **q011 (blue sky)**: filename `mountain.jpg` provided partial match; caption drift
6. **q013 (tree)**: filename `mountain.jpg` may have provided weak signal; caption has no match
7. **q017 (night scene)**: filename `Screenshot...` provided no signal; caption is fallback

## Alternative Signal Options

### Option 1: Improve Caption Quality (Recommended)

**Approach:** Reprocess corpus with stronger caption model or multi-frame captioning for better semantic coverage.

**Pros:**
- Addresses root cause (caption drift)
- Filename-agnostic
- Improves all queries, not just filename-dependent ones

**Cons:**
- Requires reprocessing
- May need model upgrade (BLIP-2 or larger BLIP variant)

**Expected impact:**
- Fixes q001, q008, q011 (caption drift cases)
- Improves q003, q010, q016 (weak semantic overlap)
- Improves q015, q017 (weak caption quality)

### Option 2: Add Query Expansion

**Approach:** Expand query terms with synonyms or related concepts before retrieval.

**Pros:**
- Filename-agnostic
- Can bridge semantic gaps ("sunset beach" → "dock", "lake", "water")

**Cons:**
- Adds complexity
- May introduce noise
- Doesn't fix caption drift

**Expected impact:**
- Improves q003, q010, q016 (weak semantic overlap)
- No effect on q001, q008, q011 (caption drift)

### Option 3: Add Visual Metadata Extraction

**Approach:** Extract visual features (dominant colors, scene type, object presence) and index them as structured metadata.

**Pros:**
- Filename-agnostic
- Can detect "blue sky", "outdoor", "indoor" without relying on captions

**Cons:**
- Significant implementation effort
- Requires additional ML models or heuristics

**Expected impact:**
- Improves q011 (blue sky detection)
- Improves q017 (night scene detection)
- No effect on caption drift cases

### Option 4: Reintroduce Filename Signal (Not Recommended)

**Approach:** Restore `_FILENAME_TOKEN_BOOST` or a variant.

**Pros:**
- Immediate metric recovery

**Cons:**
- Violates user's explicit requirement: "ignore the filename in our algorithm"
- Biases evaluation dataset
- Masks underlying caption quality issues

**Expected impact:**
- Recovers metrics to pre-regression levels
- Does not fix root cause

## Recommendation

**Primary action:** Improve caption quality by reprocessing the corpus with a stronger caption model or multi-frame captioning strategy.

**Secondary action:** Add query expansion for weak semantic overlap cases.

**Do not:** Reintroduce filename signal in any form.

## Next Steps

1. Verify caption model upgrade path (BLIP-2 or larger BLIP variant)
2. Reprocess smoke corpus with improved captioning
3. Rerun evaluation to measure caption quality impact
4. If caption improvement is insufficient, implement query expansion as a second pass
