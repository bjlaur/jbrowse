#!/usr/bin/env python3
"""
fuzzy_check_fake_cache.py

Fuzzy-ish uniqueness checker for fake Jellyfin/cache fixture JSON.

Works with either:
  1. a merged JSON file with top-level {"items": [...]}
  2. a directory containing batch_*.json files, each with {"items": [...]}

Example:
  python3 fuzzy_check_fake_cache.py fake_cache_data_merged.json
  python3 fuzzy_check_fake_cache.py batches
  python3 fuzzy_check_fake_cache.py batches --samples 100000 --threshold 0.55

This is intentionally dependency-free: stdlib only.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def load_items(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        paths = sorted(path.glob("batch_*.json"))
        if not paths:
            raise SystemExit(f"No batch_*.json files found in directory: {path}")
        items: list[dict[str, Any]] = []
        for p in paths:
            with p.open("r", encoding="ascii") as f:
                data = json.load(f)
            batch_items = data.get("items")
            if not isinstance(batch_items, list):
                raise SystemExit(f"{p} does not contain an items list")
            items.extend(batch_items)
        return items

    with path.open("r", encoding="ascii") as f:
        data = json.load(f)
    batch_items = data.get("items")
    if not isinstance(batch_items, list):
        raise SystemExit(f"{path} does not contain an items list")
    return batch_items


def extract_description(item: dict[str, Any]) -> str:
    """
    Assumes your fixture layout:
      info_lines[8...] contains description lines
      next "Genres ..." line ends the description block
    """
    lines = item.get("info_lines") or []
    if not isinstance(lines, list):
        return ""

    start = 8
    genre_i = None
    for i in range(start, len(lines)):
        line = lines[i]
        if isinstance(line, str) and line.startswith("Genres"):
            genre_i = i
            break

    if genre_i is None:
        # fallback: first few lines after the summary area
        genre_i = min(len(lines), start + 10)

    desc_lines = [
        x.strip()
        for x in lines[start:genre_i]
        if isinstance(x, str) and x.strip()
    ]
    return " ".join(desc_lines)


def count_shingles(token_lists: list[list[str]], n: int) -> Counter[tuple[str, ...]]:
    c: Counter[tuple[str, ...]] = Counter()
    for toks in token_lists:
        for i in range(max(0, len(toks) - n + 1)):
            c[tuple(toks[i:i+n])] += 1
    return c


def build_candidate_pairs(
    token_lists: list[list[str]],
    shingle8: Counter[tuple[str, ...]],
    samples: int,
    seed: int,
) -> set[tuple[int, int]]:
    """
    We do not compare all 12.5M pairs for 5,000 items by default.
    Instead:
      - random sample of pairs
      - pairs sharing same first 5 words
      - pairs sharing repeated 8-word shingles
    """
    rng = random.Random(seed)
    n = len(token_lists)
    pairs: set[tuple[int, int]] = set()

    # Random broad sample.
    for _ in range(samples):
        a, b = rng.sample(range(n), 2)
        if a > b:
            a, b = b, a
        pairs.add((a, b))

    # Same opening bucket candidates.
    buckets: defaultdict[tuple[str, ...], list[int]] = defaultdict(list)
    for i, toks in enumerate(token_lists):
        buckets[tuple(toks[:5])].append(i)

    for ids in buckets.values():
        if len(ids) > 1:
            for _ in range(min(60, len(ids) * 2)):
                a, b = rng.sample(ids, 2)
                if a > b:
                    a, b = b, a
                pairs.add((a, b))

    # Shared repeated 8-word shingles.
    shingle_to_items: defaultdict[tuple[str, ...], list[int]] = defaultdict(list)
    for i, toks in enumerate(token_lists):
        local = {
            tuple(toks[j:j+8])
            for j in range(max(0, len(toks) - 7))
        }
        for sh in local:
            count = shingle8[sh]
            # Ignore unique shingles and extremely generic huge buckets.
            if 2 <= count <= 40:
                shingle_to_items[sh].append(i)

    for ids in shingle_to_items.values():
        if len(ids) > 1:
            for _ in range(min(10, len(ids))):
                a, b = rng.sample(ids, 2)
                if a > b:
                    a, b = b, a
                pairs.add((a, b))

    return pairs


def validity_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    issues: Counter[str] = Counter()

    for item in items:
        for field in ("id", "title", "filename", "kind"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                issues[f"missing_{field}"] += 1

        kind = item.get("kind")
        if kind not in {"Movie", "Episode"}:
            issues["invalid_kind"] += 1
        elif kind == "Episode":
            if not isinstance(item.get("series_name"), str) or not item["series_name"].strip():
                issues["episode_missing_series_name"] += 1
            if not isinstance(item.get("season_number"), int):
                issues["episode_missing_season_number"] += 1
            if not isinstance(item.get("episode_number"), int):
                issues["episode_missing_episode_number"] += 1

        if not isinstance(item.get("info_lines"), list):
            issues["info_lines_not_list"] += 1
        if not isinstance(item.get("subtitle_tracks"), list):
            issues["subtitle_tracks_not_list"] += 1
            continue

        for track in item["subtitle_tracks"]:
            if not isinstance(track, dict) or not all(
                isinstance(track.get(field), str) and track[field]
                for field in ("key", "title", "mpv_sid")
            ):
                issues["invalid_subtitle_track"] += 1

    return dict(sorted(issues.items()))


def analyze(items: list[dict[str, Any]], samples: int, threshold: float, seed: int) -> dict[str, Any]:
    ids = [x.get("id", "") for x in items]
    titles = [x.get("title", "") for x in items]
    filenames = [x.get("filename", "") for x in items]
    kinds = [x.get("kind", "") for x in items]

    descs = [extract_description(x) for x in items]
    token_lists = [words(d) for d in descs]
    token_sets = [set(toks) for toks in token_lists]

    desc_counter = Counter(descs)
    sentence_counter: Counter[str] = Counter()
    first_sentence_counter: Counter[str] = Counter()

    for d in descs:
        sentences = [s.strip().lower() for s in re.split(r"[.!?]+", d) if s.strip()]
        if sentences:
            first_sentence_counter[sentences[0]] += 1
            sentence_counter.update(sentences)

    opening3 = Counter(tuple(toks[:3]) for toks in token_lists)
    opening5 = Counter(tuple(toks[:5]) for toks in token_lists)
    opening8 = Counter(tuple(toks[:8]) for toks in token_lists)
    shingle5 = count_shingles(token_lists, 5)
    shingle8 = count_shingles(token_lists, 8)

    pairs = build_candidate_pairs(token_lists, shingle8, samples=samples, seed=seed)

    threshold_counts: Counter[str] = Counter()
    worst: list[tuple[float, int, int]] = []
    sum_j = 0.0
    max_j = (0.0, None)

    thresholds = [0.40, 0.50, 0.60, 0.70, 0.80]

    for a, b in pairs:
        score = jaccard(token_sets[a], token_sets[b])
        sum_j += score

        if score > max_j[0]:
            max_j = (score, (a, b))

        for t in thresholds:
            if score >= t:
                threshold_counts[str(t)] += 1

        if score >= threshold:
            worst.append((score, a, b))

    worst.sort(reverse=True)
    worst = worst[:20]

    info_counts = [
        len(x.get("info_lines") or [])
        for x in items
    ]
    sub_counts = [
        len(x.get("subtitle_tracks") or [])
        for x in items
    ]
    desc_word_counts = [len(toks) for toks in token_lists]
    desc_sentence_counts = [
        len([s for s in re.split(r"[.!?]+", d) if s.strip()])
        for d in descs
    ]

    return {
        "validity_issues": validity_summary(items),
        "items": len(items),
        "movies": sum(1 for k in kinds if k == "Movie"),
        "episodes": sum(1 for k in kinds if k == "Episode"),

        "unique_ids": len(set(ids)),
        "duplicate_ids": len(ids) - len(set(ids)),
        "unique_titles": len(set(titles)),
        "duplicate_titles": len(titles) - len(set(titles)),
        "unique_filenames": len(set(filenames)),
        "duplicate_filenames": len(filenames) - len(set(filenames)),

        "unique_descriptions": len(set(descs)),
        "duplicate_descriptions": len(descs) - len(set(descs)),
        "max_description_reuse": max(desc_counter.values()) if desc_counter else 0,

        "description_words_avg": round(statistics.mean(desc_word_counts), 1) if desc_word_counts else 0,
        "description_words_median": statistics.median(desc_word_counts) if desc_word_counts else 0,
        "description_words_min": min(desc_word_counts) if desc_word_counts else 0,
        "description_words_max": max(desc_word_counts) if desc_word_counts else 0,

        "description_sentences_avg": round(statistics.mean(desc_sentence_counts), 2) if desc_sentence_counts else 0,
        "description_sentences_min": min(desc_sentence_counts) if desc_sentence_counts else 0,
        "description_sentences_max": max(desc_sentence_counts) if desc_sentence_counts else 0,

        "unique_sentences": len(sentence_counter),
        "total_sentences": sum(sentence_counter.values()),
        "max_sentence_reuse": max(sentence_counter.values()) if sentence_counter else 0,

        "unique_first_sentences": len(first_sentence_counter),
        "max_first_sentence_reuse": max(first_sentence_counter.values()) if first_sentence_counter else 0,

        "unique_opening_3grams": len(opening3),
        "max_opening_3gram_reuse": max(opening3.values()) if opening3 else 0,
        "unique_opening_5grams": len(opening5),
        "max_opening_5gram_reuse": max(opening5.values()) if opening5 else 0,
        "unique_opening_8grams": len(opening8),
        "max_opening_8gram_reuse": max(opening8.values()) if opening8 else 0,

        "unique_5word_shingles": len(shingle5),
        "max_5word_shingle_reuse": max(shingle5.values()) if shingle5 else 0,
        "unique_8word_shingles": len(shingle8),
        "max_8word_shingle_reuse": max(shingle8.values()) if shingle8 else 0,

        "candidate_pairs_checked": len(pairs),
        "avg_token_jaccard": round(sum_j / len(pairs), 3) if pairs else 0,
        "max_token_jaccard": round(max_j[0], 3),
        "jaccard_threshold_counts": dict(threshold_counts),

        "items_with_subtitles": sum(1 for c in sub_counts if c > 0),
        "total_subtitle_tracks": sum(sub_counts),
        "max_subtitle_tracks": max(sub_counts) if sub_counts else 0,

        "avg_info_lines": round(statistics.mean(info_counts), 1) if info_counts else 0,
        "median_info_lines": statistics.median(info_counts) if info_counts else 0,
        "max_info_lines": max(info_counts) if info_counts else 0,

        "worst_pairs_preview": [
            {
                "jaccard": round(score, 3),
                "a_index": a,
                "b_index": b,
                "a_title": str(titles[a])[:140],
                "b_title": str(titles[b])[:140],
                "a_desc": descs[a][:350],
                "b_desc": descs[b][:350],
            }
            for score, a, b in worst
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="merged JSON file or directory containing batch_*.json")
    parser.add_argument("--samples", type=int, default=50000, help="random pair sample count")
    parser.add_argument("--threshold", type=float, default=0.55, help="include worst-pair previews at or above this Jaccard score")
    parser.add_argument("--seed", type=int, default=2002)
    parser.add_argument("--out", default="", help="optional report JSON output path")
    args = parser.parse_args()

    path = Path(args.input)
    items = load_items(path)
    if not all(isinstance(item, dict) for item in items):
        raise SystemExit("Every item must be a JSON object")
    report = analyze(items, samples=args.samples, threshold=args.threshold, seed=args.seed)

    text = json.dumps(report, indent=2)
    print(text)

    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
