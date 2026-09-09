"""
Advanced NLP Engine for Meeting Summarization
Uses spaCy + NLTK for multi-level summaries, decision detection,
smart task extraction, topic segmentation, risk detection, and productivity scoring.
"""
import re
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import spacy
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import config

# ── Initialize NLP resources ──
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)

try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    _nlp = spacy.load("en_core_web_sm")

STOP_WORDS = set(stopwords.words("english"))

# ── Sentiment Lexicons ──
POSITIVE_WORDS = {
    "good", "great", "excellent", "fantastic", "wonderful", "amazing", "awesome",
    "perfect", "outstanding", "brilliant", "happy", "positive", "success",
    "successful", "achieve", "accomplished", "approve", "approved", "agree",
    "agreed", "confirmed", "finalized", "completed", "done", "ready", "excited",
    "confident", "efficient", "effective", "innovative", "valuable", "helpful",
    "clear", "productive", "progress", "opportunity", "growth", "improve",
    "improved", "support", "solution", "resolved", "fixed", "smooth", "strong",
    "benefit", "advantage", "recommend", "promising", "optimistic", "pleased",
}
NEGATIVE_WORDS = {
    "bad", "poor", "terrible", "horrible", "awful", "negative", "failure",
    "failed", "problem", "issue", "concern", "worry", "worried", "delay",
    "delayed", "blocking", "blocked", "stuck", "difficult", "challenge",
    "challenging", "confused", "unclear", "uncertain", "risk", "risky",
    "critical", "urgent", "behind", "missed", "mistake", "error", "bug",
    "broken", "missing", "incomplete", "unfinished", "overdue", "late",
    "slow", "expensive", "conflict", "disagree", "reject", "rejected",
    "denied", "obstacle", "threat", "danger", "shortage", "turnover",
}


class MeetingAnalyzer:
    """Full meeting analysis pipeline."""

    def __init__(self):
        self.nlp = _nlp

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    def analyze(self, transcript: str) -> dict:
        """Run full analysis pipeline on a meeting transcript."""
        if not transcript or len(transcript.strip()) < 50:
            return {"error": "Transcript too short. Please provide at least 50 characters."}

        # Parse speakers
        speakers, utterances = self._parse_speakers(transcript)
        has_speakers = len(speakers) > 0
        body_text = " ".join(u["speech"] for u in utterances) if has_speakers else transcript

        # spaCy doc on full text
        doc = self.nlp(body_text)

        # Run all analysis modules
        sentences = sent_tokenize(transcript)
        short_summary = self._summarize(transcript, config.SHORT_SUMMARY_SENTENCES)
        detailed_summary = self._summarize(transcript, config.DETAILED_SUMMARY_SENTENCES)
        bullet_points = self._extract_bullet_points(transcript, config.BULLET_POINTS_COUNT)
        decisions = self._detect_decisions(transcript)
        tasks = self._extract_tasks(transcript, speakers, doc)
        topics = self._segment_topics(transcript)
        keywords = self._extract_keywords(body_text)
        risks = self._detect_risks(transcript)
        participants = self._analyze_participants(speakers, utterances) if has_speakers else []
        sentiment = self._analyze_sentiment(body_text)
        speaker_sentiments = self._speaker_sentiments(speakers) if has_speakers else {}
        readability = self._readability(transcript)
        stats = self._compute_stats(transcript, utterances, sentences)
        productivity_score = self._compute_productivity_score(
            tasks, decisions, participants, sentences, risks, readability
        )

        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "bullet_points": bullet_points,
            "decisions": decisions,
            "tasks": tasks,
            "topics": topics,
            "keywords": keywords,
            "risks": risks,
            "participants": participants,
            "sentiment": sentiment,
            "speaker_sentiments": speaker_sentiments,
            "readability": readability,
            "stats": stats,
            "productivity_score": productivity_score,
            "speakers": speakers,
            "utterances": utterances,
            "has_speakers": has_speakers,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_hierarchical(self, transcript: str, chunk_chars: int = None) -> dict:
        """Analyze all transcript chunks, then aggregate their evidence.

        This keeps long meetings complete while ensuring the expensive NLP and
        optional LLM layers receive bounded pieces of text.
        """
        chunk_chars = chunk_chars or config.TRANSCRIPT_CHUNK_CHARS
        if len(transcript) <= chunk_chars:
            return self.analyze(transcript)

        chunks = []
        start = 0
        while start < len(transcript):
            end = min(start + chunk_chars, len(transcript))
            if end < len(transcript):
                boundary = transcript.rfind("\n", start, end)
                if boundary > start + chunk_chars // 2:
                    end = boundary
            chunk_text = transcript[start:end].strip()
            if chunk_text:
                chunk_result = self.analyze(chunk_text)
                if "error" not in chunk_result:
                    chunks.append(chunk_result)
            start = end

        if not chunks:
            return {"error": "Transcript could not be divided into analyzable sections."}

        compact_context = "\n\n".join(
            f"Chunk {index}: {chunk.get('short_summary', '')} "
            f"Key points: {'; '.join(chunk.get('bullet_points', [])[:4])}"
            for index, chunk in enumerate(chunks, start=1)
        )
        global_result = self.analyze(compact_context)
        global_result["decisions"] = self._merge_text_items(
            item for chunk in chunks for item in chunk.get("decisions", [])
        )
        global_result["tasks"] = self._merge_tasks(
            task for chunk in chunks for task in chunk.get("tasks", [])
        )
        global_result["risks"] = self._merge_risks(
            risk for chunk in chunks for risk in chunk.get("risks", [])
        )
        global_result["chunk_summaries"] = [
            {"index": index, "summary": chunk.get("short_summary", "")}
            for index, chunk in enumerate(chunks, start=1)
        ]
        global_result["source_chunk_count"] = len(chunks)
        global_result["source_char_count"] = len(transcript)
        global_result["stats"]["word_count"] = len(transcript.split())
        return global_result

    def _merge_text_items(self, items) -> list:
        merged = []
        for item in items:
            if item and not any(self._jaccard(item, existing) > 0.65 for existing in merged):
                merged.append(item)
        return merged

    def _merge_tasks(self, tasks) -> list:
        merged = []
        for task in tasks:
            if not task.get("task"):
                continue
            duplicate = next(
                (existing for existing in merged
                 if self._jaccard(task["task"], existing["task"]) > 0.65),
                None,
            )
            if duplicate:
                if duplicate.get("deadline") == "Not specified" and task.get("deadline") != "Not specified":
                    duplicate["deadline"] = task["deadline"]
                if duplicate.get("assignee") == "Team" and task.get("assignee") != "Team":
                    duplicate["assignee"] = task["assignee"]
            else:
                merged.append(dict(task))
        return merged

    def _merge_risks(self, risks) -> list:
        merged = []
        for risk in risks:
            description = risk.get("description", "")
            if description and not any(self._jaccard(description, existing.get("description", "")) > 0.65 for existing in merged):
                merged.append(dict(risk))
        return merged

    # ═══════════════════════════════════════════
    #  SPEAKER PARSING
    # ═══════════════════════════════════════════

    def _parse_speakers(self, text: str) -> tuple:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        speakers = defaultdict(list)
        utterances = []
        patterns = [
            re.compile(r"^([A-Z][a-zA-Z\s]{1,25}):\s*(.+)"),
            re.compile(r"^\[([A-Z][a-zA-Z\s]{1,25})\]\s*(.+)"),
            re.compile(r"^([A-Z][a-zA-Z\s]{1,25})\s*[-–—]\s*(.+)"),
        ]
        for line in lines:
            matched = False
            for pat in patterns:
                m = pat.match(line)
                if m:
                    spk, speech = m.group(1).strip(), m.group(2).strip()
                    speakers[spk].append(speech)
                    utterances.append({"speaker": spk, "speech": speech})
                    matched = True
                    break
            if not matched and utterances:
                utterances[-1]["speech"] += " " + line
                last_spk = utterances[-1]["speaker"]
                speakers[last_spk][-1] += " " + line
        return dict(speakers), utterances

    # ═══════════════════════════════════════════
    #  MULTI-LEVEL SUMMARIES
    # ═══════════════════════════════════════════

    def _summarize(self, text: str, n: int = 5) -> str:
        """TF-IDF extractive summarization with positional weighting."""
        sentences = sent_tokenize(text)
        if len(sentences) <= n:
            return " ".join(sentences)

        # Build TF-IDF matrix
        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
            tfidf_matrix = vectorizer.fit_transform(sentences)
        except ValueError:
            return " ".join(sentences[:n])

        # Score each sentence
        scores = []
        for i, sent in enumerate(sentences):
            tfidf_score = float(tfidf_matrix[i].sum())
            # Positional weighting
            if i == 0 or i == len(sentences) - 1:
                pos_w = 1.4
            elif i < len(sentences) * 0.2:
                pos_w = 1.2
            else:
                pos_w = 1.0
            # Length penalty
            words = len(sent.split())
            len_w = 0.5 if words < 5 else (0.8 if words > 50 else 1.0)
            scores.append((i, tfidf_score * pos_w * len_w, sent))

        # Select top N, maintain original order
        top = sorted(scores, key=lambda x: x[1], reverse=True)[:n]
        top = sorted(top, key=lambda x: x[0])
        return " ".join(t[2].strip() for t in top)

    def _extract_bullet_points(self, text: str, n: int = 8) -> list:
        """Extract key bullet points from the transcript."""
        sentences = sent_tokenize(text)
        if len(sentences) <= n:
            return [s.strip() for s in sentences]

        importance_patterns = [
            re.compile(r"\b(important|critical|key|main|primary|major|significant|essential)\b", re.I),
            re.compile(r"\b(decided|agreed|approved|confirmed|action|task|deadline)\b", re.I),
            re.compile(r"\b(budget|cost|revenue|timeline|launch|release|milestone)\b", re.I),
            re.compile(r"\b(issue|problem|concern|risk|blocker|challenge)\b", re.I),
            re.compile(r"\b(recommend|propose|suggest|plan|strategy)\b", re.I),
        ]
        scored = []
        for sent in sentences:
            score = sum(2 for p in importance_patterns if p.search(sent))
            words = [w.lower() for w in word_tokenize(sent) if w.isalpha() and w.lower() not in STOP_WORDS]
            score += len(words) * 0.05
            if len(sent.split()) < 5:
                score *= 0.3
            scored.append((score, sent.strip()))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:n] if len(s[1]) > 15]

    # ═══════════════════════════════════════════
    #  DECISION DETECTION
    # ═══════════════════════════════════════════

    def _detect_decisions(self, text: str) -> list:
        """Detect decisions using multiple regex patterns."""
        sentences = sent_tokenize(text)
        patterns = [re.compile(p, re.I) for p in config.DECISION_PATTERNS]
        decisions = []
        seen = set()
        for sent in sentences:
            if any(p.search(sent) for p in patterns):
                clean = sent.strip()
                if clean not in seen and len(clean) > 15:
                    seen.add(clean)
                    decisions.append(clean)
        return decisions

    # ═══════════════════════════════════════════
    #  SMART TASK EXTRACTION
    # ═══════════════════════════════════════════

    def _extract_tasks(self, text: str, speakers: dict, doc) -> list:
        """Extract tasks with person, description, deadline, and priority."""
        sentences = sent_tokenize(text)
        action_patterns = [re.compile(p, re.I) for p in config.ACTION_PATTERNS]
        speaker_names = list(speakers.keys())

        # Get date entities from spaCy
        date_entities = {}
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME"):
                date_entities[ent.text.lower()] = ent.text

        tasks = []
        seen_tasks = set()

        for sent in sentences:
            if not any(p.search(sent) for p in action_patterns):
                continue
            if len(sent.split()) < 5:
                continue

            # Deduplicate
            sent_key = sent.strip().lower()[:80]
            if sent_key in seen_tasks:
                continue

            # Check similarity with existing
            if any(self._jaccard(sent, t["task"]) > 0.65 for t in tasks):
                continue
            seen_tasks.add(sent_key)

            # Extract assignee
            assignee = "Team"
            for name in speaker_names:
                first_name = name.split()[0]
                if re.search(rf"\b{re.escape(first_name)}\b", sent, re.I):
                    assignee = name
                    break
            # Also check spaCy PERSON entities
            sent_doc = self.nlp(sent)
            for ent in sent_doc.ents:
                if ent.label_ == "PERSON" and assignee == "Team":
                    # Match against known speakers
                    for name in speaker_names:
                        if ent.text.lower() in name.lower() or name.lower() in ent.text.lower():
                            assignee = name
                            break

            # Extract deadline
            deadline = self._extract_deadline(sent, sent_doc)

            # Determine priority
            priority = self._determine_priority(sent)

            tasks.append({
                "task": sent.strip(),
                "assignee": assignee,
                "deadline": deadline,
                "priority": priority,
                "status": "pending",
            })

        return tasks

    def _extract_deadline(self, sent: str, doc) -> str:
        """Extract deadline using spaCy NER + regex fallback."""
        # spaCy DATE entities
        for ent in doc.ents:
            if ent.label_ == "DATE":
                return ent.text

        # Regex fallback
        date_patterns = [
            re.compile(r"\b(by\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I),
            re.compile(r"\b(by\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b", re.I),
            re.compile(r"\b(by\s+)?(end\s+of\s+(?:day|week|month|quarter|year|this\s+week))\b", re.I),
            re.compile(r"\b(by\s+)?(tomorrow|today|tonight|eod|asap|next\s+\w+)\b", re.I),
            re.compile(r"\b(by\s+)?(\d{1,2}/\d{1,2}/\d{2,4})\b"),
            re.compile(r"\b(by\s+)?(Q[1-4]\s*\d{4})\b", re.I),
        ]
        for pat in date_patterns:
            m = pat.search(sent)
            if m:
                result = m.group(0).strip()
                result = re.sub(r"^by\s+", "", result, flags=re.I)
                return result.strip().title()

        return "Not specified"

    def _determine_priority(self, sent: str) -> str:
        """Determine task priority based on keywords."""
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in config.HIGH_PRIORITY_KEYWORDS):
            return "high"
        if any(kw in sent_lower for kw in config.MEDIUM_PRIORITY_KEYWORDS):
            return "medium"
        return "low"

    # ═══════════════════════════════════════════
    #  TOPIC SEGMENTATION
    # ═══════════════════════════════════════════

    def _segment_topics(self, text: str) -> list:
        """Segment meeting into topics using TF-IDF + cosine similarity."""
        sentences = sent_tokenize(text)
        if len(sentences) < 4:
            return [{"topic": "General Discussion", "sentences": sentences, "keywords": []}]

        # TF-IDF for sentences
        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=3000)
            tfidf = vectorizer.fit_transform(sentences)
        except ValueError:
            return [{"topic": "General Discussion", "sentences": sentences, "keywords": []}]

        # Calculate similarity between consecutive sentences
        similarities = []
        for i in range(len(sentences) - 1):
            sim = cosine_similarity(tfidf[i], tfidf[i + 1])[0][0]
            similarities.append(sim)

        # Find topic boundaries (low similarity = topic change)
        threshold = np.mean(similarities) - 0.5 * np.std(similarities) if similarities else 0.1
        min_segment = max(2, len(sentences) // 10)

        segments = []
        current = [sentences[0]]
        for i, sim in enumerate(similarities):
            if sim < threshold and len(current) >= min_segment:
                segments.append(current)
                current = [sentences[i + 1]]
            else:
                current.append(sentences[i + 1])
        if current:
            segments.append(current)

        # Label each segment
        topics = []
        for seg in segments[:config.MAX_TOPICS]:
            seg_text = " ".join(seg)
            kws = self._extract_keywords(seg_text, top=3)
            topic_name = " / ".join(k["word"].title() for k in kws) if kws else "Discussion"
            topics.append({
                "topic": topic_name,
                "sentences": seg,
                "keywords": [k["word"] for k in kws],
            })
        return topics

    # ═══════════════════════════════════════════
    #  KEYWORD EXTRACTION
    # ═══════════════════════════════════════════

    def _extract_keywords(self, text: str, top: int = 20) -> list:
        """Extract keywords using TF-IDF scoring."""
        words = [w.lower() for w in word_tokenize(text) if w.isalpha() and len(w) > 3 and w.lower() not in STOP_WORDS]
        freq = Counter(words)
        return [{"word": w, "count": c} for w, c in freq.most_common(top)]

    # ═══════════════════════════════════════════
    #  RISK DETECTION
    # ═══════════════════════════════════════════

    def _detect_risks(self, text: str) -> list:
        """Detect risks mentioned in the meeting."""
        sentences = sent_tokenize(text)
        risk_patterns = [
            re.compile(r"\b(risk|risky|at risk)\b", re.I),
            re.compile(r"\b(concern|worried|worry|fear)\b", re.I),
            re.compile(r"\b(delay|delayed|slipping|behind\s+schedule)\b", re.I),
            re.compile(r"\b(blocking|blocked|blocker|obstacle|bottleneck)\b", re.I),
            re.compile(r"\b(budget\s+overrun|over\s+budget|cost\s+increase)\b", re.I),
            re.compile(r"\b(missing|missed|miss)\s+\w+\s*(deadline|window|date|target)\b", re.I),
            re.compile(r"\b(worst\s+case|if\s+(?:we|this)\s+(?:don'?t|fail|can'?t))\b", re.I),
            re.compile(r"\b(security|vulnerability|compliance|legal)\s+\w*\s*(issue|concern|risk|problem)?\b", re.I),
        ]
        risks = []
        seen = set()
        for sent in sentences:
            match_count = sum(1 for p in risk_patterns if p.search(sent))
            if match_count > 0:
                clean = sent.strip()
                if clean not in seen and len(clean) > 15:
                    severity = "high" if match_count >= 2 else ("medium" if match_count == 1 and any(
                        kw in clean.lower() for kw in ["critical", "blocker", "urgent", "worst case"]
                    ) else "low")
                    seen.add(clean)
                    risks.append({
                        "description": clean,
                        "severity": severity,
                        "keywords": [kw for kw in config.RISK_KEYWORDS if kw in clean.lower()],
                    })
        return risks

    # ═══════════════════════════════════════════
    #  PARTICIPANT CONTRIBUTION ANALYSIS
    # ═══════════════════════════════════════════

    def _analyze_participants(self, speakers: dict, utterances: list) -> list:
        """Analyze each participant's contribution."""
        total_words = sum(len(speech.split()) for speeches in speakers.values() for speech in speeches)
        total_utterances = len(utterances)

        participants = []
        for name, speeches in speakers.items():
            word_count = sum(len(s.split()) for s in speeches)
            utterance_count = len(speeches)
            full_text = " ".join(speeches)

            # Sentiment per speaker
            sentiment = self._analyze_sentiment(full_text)

            # Topics contributed to
            topic_keywords = self._extract_keywords(full_text, top=5)

            participants.append({
                "name": name,
                "utterance_count": utterance_count,
                "word_count": word_count,
                "contribution_pct": round((word_count / max(total_words, 1)) * 100, 1),
                "avg_utterance_length": round(word_count / max(utterance_count, 1), 1),
                "sentiment": sentiment,
                "top_keywords": [k["word"] for k in topic_keywords],
            })

        participants.sort(key=lambda p: p["word_count"], reverse=True)
        return participants

    # ═══════════════════════════════════════════
    #  SENTIMENT ANALYSIS
    # ═══════════════════════════════════════════

    def _analyze_sentiment(self, text: str) -> dict:
        """Lexicon-based sentiment analysis."""
        words = [w.lower() for w in word_tokenize(text) if w.isalpha()]
        pos = sum(1 for w in words if w in POSITIVE_WORDS)
        neg = sum(1 for w in words if w in NEGATIVE_WORDS)
        total = max(len(words), 1)
        score = (pos - neg) / total
        if score > 0.02:
            label = "positive"
        elif score < -0.02:
            label = "negative"
        else:
            label = "neutral"
        return {"positive": pos, "negative": neg, "score": round(score, 4), "label": label, "total": total}

    def _speaker_sentiments(self, speakers: dict) -> dict:
        """Sentiment per speaker."""
        result = {}
        for name, speeches in speakers.items():
            full = " ".join(speeches)
            s = self._analyze_sentiment(full)
            s["count"] = len(speeches)
            result[name] = s
        return result

    # ═══════════════════════════════════════════
    #  READABILITY
    # ═══════════════════════════════════════════

    def _readability(self, text: str) -> dict:
        """Flesch-Kincaid readability score."""
        words = [w for w in word_tokenize(text) if w.isalpha()]
        sentences = sent_tokenize(text)
        syllable_count = sum(self._count_syllables(w) for w in words)
        word_count = max(len(words), 1)
        sent_count = max(len(sentences), 1)

        fk = 206.835 - (1.015 * word_count / sent_count) - (84.6 * syllable_count / word_count)
        score = max(0, min(100, round(fk)))
        if score > 70:
            label = "Easy"
        elif score > 50:
            label = "Moderate"
        else:
            label = "Complex"
        return {"score": score, "label": label}

    def _count_syllables(self, word: str) -> int:
        word = word.lower()
        word = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", word)
        word = re.sub(r"^y", "", word)
        matches = re.findall(r"[aeiouy]{1,2}", word)
        return max(1, len(matches))

    # ═══════════════════════════════════════════
    #  STATS
    # ═══════════════════════════════════════════

    def _compute_stats(self, text: str, utterances: list, sentences: list) -> dict:
        words = [w for w in word_tokenize(text) if w.isalpha()]
        speakers_set = set(u["speaker"] for u in utterances) if utterances else set()
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "speaker_count": len(speakers_set),
            "utterance_count": len(utterances),
            "estimated_duration": round(len(words) / 130),
            "avg_sentence_length": round(len(words) / max(len(sentences), 1), 1),
        }

    # ═══════════════════════════════════════════
    #  PRODUCTIVITY SCORE
    # ═══════════════════════════════════════════

    def _compute_productivity_score(self, tasks, decisions, participants, sentences, risks, readability) -> dict:
        """Composite meeting productivity score (0-100)."""
        sent_count = max(len(sentences), 1)

        # Action density (0-25): more tasks per sentence = more productive
        action_density = min(len(tasks) / sent_count * 50, 1.0) * 25

        # Decision ratio (0-25): decisions made relative to discussion
        decision_ratio = min(len(decisions) / sent_count * 30, 1.0) * 25

        # Participation balance (0-25): how evenly distributed
        if participants:
            contributions = [p["contribution_pct"] for p in participants]
            max_contrib = max(contributions) if contributions else 100
            balance = 1.0 - (max_contrib - 100 / max(len(participants), 1)) / 100
            participation_score = max(0, min(1, balance)) * 25
        else:
            participation_score = 12.5  # neutral

        # Risk awareness (0-15): identifying risks is productive
        risk_score = min(len(risks) / 3, 1.0) * 15

        # Clarity (0-10): based on readability
        clarity_score = (readability["score"] / 100) * 10

        total = round(action_density + decision_ratio + participation_score + risk_score + clarity_score)
        total = max(0, min(100, total))

        if total >= 75:
            grade = "A"
            label = "Excellent"
        elif total >= 60:
            grade = "B"
            label = "Good"
        elif total >= 45:
            grade = "C"
            label = "Average"
        elif total >= 30:
            grade = "D"
            label = "Below Average"
        else:
            grade = "F"
            label = "Needs Improvement"

        return {
            "total": total,
            "grade": grade,
            "label": label,
            "breakdown": {
                "action_density": round(action_density, 1),
                "decision_ratio": round(decision_ratio, 1),
                "participation_balance": round(participation_score, 1),
                "risk_awareness": round(risk_score, 1),
                "clarity": round(clarity_score, 1),
            },
        }

    # ═══════════════════════════════════════════
    #  UTILITY
    # ═══════════════════════════════════════════

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa = set(a.lower().split())
        sb = set(b.lower().split())
        inter = sa & sb
        uni = sa | sb
        return len(inter) / max(len(uni), 1)
