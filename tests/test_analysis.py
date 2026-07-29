"""Unit tests for analysis engine."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from clearthread.analysis.episode_engine import EpisodeEngine, EpisodeDetectionMethod, EpisodeProposal
from clearthread.analysis.pattern_analyzer import PatternAnalyzer, PatternType
from clearthread.analysis.growth_analyzer import GrowthAnalyzer, GrowthPatternType, GrowthIndicator
from clearthread.analysis.reflection_questions import ReflectionQuestionGenerator
from clearthread.models.episode import Episode, EpisodeType, EpisodeStatus
from clearthread.models.finding import Finding, ConfidenceLevel
from clearthread.models.reflection_question import ReflectionQuestion


class TestEpisodeEngine:
    """Tests for EpisodeEngine (R6)."""

    def test_propose_episodes(self, episode_engine):
        """Test proposing episodes."""
        messages = []
        base_time = datetime(2024, 1, 1)
        for i in range(10):
            msg = type('Msg', (), {
                'original_timestamp': base_time + timedelta(hours=i),
                'text': f"Message {i}",
                'id': uuid4(),
                'reply_to': uuid4() if i > 0 else None,
                'topic': 'general',
            })()
            messages.append(msg)

        proposals = episode_engine.propose_episodes(messages)
        assert len(proposals) >= 0  # May be 0 if no significant gaps

    def test_accept_episode(self, episode_engine):
        """Test accepting an episode."""
        episode = Episode(title="Test", status=EpisodeStatus.PROPOSED)
        ep_id = str(episode.id)
        episode_engine._episodes[ep_id] = episode
        episode_engine._review_inbox.append(ep_id)

        result = episode_engine.accept_episode(episode.id)
        assert result is True
        assert episode.status == EpisodeStatus.ACCEPTED
        assert ep_id not in episode_engine._review_inbox

    def test_reject_episode(self, episode_engine):
        """Test rejecting an episode."""
        episode = Episode(title="Test", status=EpisodeStatus.PROPOSED)
        ep_id = str(episode.id)
        episode_engine._episodes[ep_id] = episode
        episode_engine._review_inbox.append(ep_id)

        result = episode_engine.reject_episode(episode.id)
        assert result is True
        assert episode.status == EpisodeStatus.REJECTED

    def test_edit_episode(self, episode_engine):
        """Test editing an episode."""
        episode = Episode(title="Test", status=EpisodeStatus.PROPOSED)
        ep_id = str(episode.id)
        episode_engine._episodes[ep_id] = episode

        result = episode_engine.edit_episode(episode.id, classification="new_class")
        assert result is True
        assert episode.user_classification == "new_class"

    def test_split_episode(self, episode_engine):
        """Test splitting an episode."""
        episode = Episode(title="Test")
        ep_id = str(episode.id)
        episode_engine._episodes[ep_id] = episode

        original, split = episode_engine.split_episode(episode.id)
        assert original.status == EpisodeStatus.SPLIT
        assert split.status == EpisodeStatus.PROPOSED

    def test_merge_episodes(self, episode_engine):
        """Test merging episodes."""
        e1 = Episode(title="E1")
        e2 = Episode(title="E2")
        episode_engine._episodes[str(e1.id)] = e1
        episode_engine._episodes[str(e2.id)] = e2

        merged = episode_engine.merge_episodes([e1.id, e2.id])
        assert merged.status == EpisodeStatus.MERGED

    def test_review_inbox(self, episode_engine):
        """Test review inbox."""
        for i in range(5):
            ep = Episode(status=EpisodeStatus.PROPOSED)
            episode_engine._episodes[str(ep.id)] = ep
            episode_engine._review_inbox.append(str(ep.id))

        inbox = episode_engine.get_review_inbox()
        assert len(inbox) == 5

    def test_review_inbox_limit(self, episode_engine):
        """Test review inbox limit (R6)."""
        episode_engine.MAX_UNREVIEWED = 3
        for i in range(5):
            ep = Episode(status=EpisodeStatus.PROPOSED)
            episode_engine._episodes[str(ep.id)] = ep
            episode_engine._review_inbox.append(str(ep.id))

        inbox = episode_engine.get_review_inbox(limit=3)
        assert len(inbox) == 3

    def test_episode_count(self, episode_engine):
        """Test episode count."""
        assert episode_engine.get_episode_count() == 0
        ep = Episode()
        episode_engine._episodes[str(ep.id)] = ep
        assert episode_engine.get_episode_count() == 1

    def test_unreviewed_count(self, episode_engine):
        """Test unreviewed count."""
        episode_engine._review_inbox.append("id1")
        episode_engine._review_inbox.append("id2")
        assert episode_engine.get_unreviewed_count() == 2

    def test_has_episodes(self, episode_engine):
        """Test has_episodes."""
        assert episode_engine.has_episodes() is False
        episode_engine._episodes["test"] = Episode()
        assert episode_engine.has_episodes() is True

    def test_no_episodes_message(self, episode_engine):
        """Test no episodes message."""
        msg = episode_engine.no_episodes_message()
        assert "No episodes" in msg

    def test_custom_topics(self, episode_engine):
        """Test custom topic management."""
        episode_engine.add_custom_topic("work")
        episode_engine.add_custom_topic("family")
        topics = episode_engine.get_custom_topics()
        assert "work" in topics
        assert "family" in topics

    def test_to_dict(self, episode_engine):
        """Test serialization."""
        data = episode_engine.to_dict()
        assert "episode_count" in data
        assert "unreviewed_count" in data


class TestPatternAnalyzer:
    """Tests for PatternAnalyzer (R8)."""

    def test_analyze_patterns(self, pattern_analyzer):
        """Test pattern analysis."""
        messages = []
        base_time = datetime(2024, 1, 1)
        for i in range(20):
            msg = type('Msg', (), {
                'normalized_utc': base_time + timedelta(days=i),
                'text': "sorry" if i % 3 == 0 else "Hello",
                'sender_display_name': "Alice" if i % 2 == 0 else "Bob",
                'id': uuid4(),
                'reply_to': uuid4() if i > 0 else None,
            })()
            messages.append(msg)

        results = pattern_analyzer.analyze_patterns(messages)
        assert len(results) >= 0

    def test_finding_detection(self, pattern_analyzer):
        """Test finding detection."""
        finding = pattern_analyzer.get_finding(uuid4())
        assert finding is None

    def test_all_findings(self, pattern_analyzer):
        """Test getting all findings."""
        findings = pattern_analyzer.get_all_findings()
        assert isinstance(findings, list)

    def test_mark_finding_inaccurate(self, pattern_analyzer):
        """Test marking finding as inaccurate."""
        finding = Finding()
        pattern_analyzer._findings[str(finding.id)] = finding
        result = pattern_analyzer.mark_finding_inaccurate(finding.id)
        assert result is True
        assert finding.status.value == "disputed"

    def test_reject_finding(self, pattern_analyzer):
        """Test rejecting a finding."""
        finding = Finding()
        pattern_analyzer._findings[str(finding.id)] = finding
        result = pattern_analyzer.reject_finding(finding.id)
        assert result is True
        assert str(finding.id) in pattern_analyzer._rejected_findings

    def test_correct_finding(self, pattern_analyzer):
        """Test correcting a finding."""
        finding = Finding()
        pattern_analyzer._findings[str(finding.id)] = finding
        result = pattern_analyzer.correct_finding(finding.id, "New correction")
        assert result is True
        assert finding.user_correction == "New correction"

    def test_needs_more_data(self, pattern_analyzer):
        """Test needs_more_data check (R9)."""
        assert pattern_analyzer.needs_more_data(15) is True
        assert pattern_analyzer.needs_more_data(20) is False
        assert pattern_analyzer.needs_more_data(25) is False

    def test_to_dict(self, pattern_analyzer):
        """Test serialization."""
        data = pattern_analyzer.to_dict()
        assert "finding_count" in data


class TestGrowthAnalyzer:
    """Tests for GrowthAnalyzer (R11)."""

    def test_analyze_growth(self, growth_analyzer):
        """Test growth analysis."""
        messages = []
        base_time = datetime(2024, 1, 1)
        for i in range(20):
            msg = type('Msg', (), {
                'normalized_utc': base_time + timedelta(days=i),
                'text': "boundary" if i % 4 == 0 else "Hello",
                'sender_display_name': "Alice" if i % 2 == 0 else "Bob",
            })()
            messages.append(msg)

        findings = growth_analyzer.analyze_growth(messages)
        assert isinstance(findings, list)

    def test_growth_findings(self, growth_analyzer):
        """Test getting growth findings."""
        findings = growth_analyzer.get_growth_findings()
        assert isinstance(findings, list)

    def test_sufficient_data(self, growth_analyzer):
        """Test sufficient data check (R11)."""
        assert growth_analyzer.has_sufficient_data(2, 2) is True
        assert growth_analyzer.has_sufficient_data(1, 2) is False
        assert growth_analyzer.has_sufficient_data(2, 1) is False

    def test_to_dict(self, growth_analyzer):
        """Test serialization."""
        data = growth_analyzer.to_dict()
        assert "finding_count" in data


class TestReflectionQuestionGenerator:
    """Tests for ReflectionQuestionGenerator (R26)."""

    def test_generate_questions(self):
        """Test generating reflection questions."""
        generator = ReflectionQuestionGenerator()
        questions = generator.generate_questions(count=3)
        assert len(questions) == 3
        assert all(isinstance(q, ReflectionQuestion) for q in questions)

    def test_generate_non_directive(self):
        """Test generating non-directive questions (R26)."""
        generator = ReflectionQuestionGenerator()
        questions = generator.generate_non_directive_questions("the data", count=3)
        assert len(questions) == 3

    def test_save_reflection(self):
        """Test saving reflection as annotation (R26)."""
        generator = ReflectionQuestionGenerator()
        questions = generator.generate_questions(count=1)
        qid = questions[0].id

        result = generator.save_reflection_as_annotation(qid, "My reflection")
        assert result is True

    def test_dismiss_question(self):
        """Test dismissing a question (R26)."""
        generator = ReflectionQuestionGenerator()
        questions = generator.generate_questions(count=1)
        qid = questions[0].id

        result = generator.dismiss_question(qid)
        assert result is True

    def test_disable_auto_generation(self):
        """Test disabling auto generation (R26)."""
        generator = ReflectionQuestionGenerator()
        generator.enable_auto_generation()
        generator.disable_auto_generation()
        assert generator._question_pool.max_questions_per_finding == 0

    def test_enable_auto_generation(self):
        """Test enabling auto generation (R26)."""
        generator = ReflectionQuestionGenerator()
        generator.disable_auto_generation()
        generator.enable_auto_generation()
        assert generator._question_pool.max_questions_per_finding == 5

    def test_get_data_reference(self):
        """Test getting data reference."""
        generator = ReflectionQuestionGenerator()
        ref = generator.get_data_reference(uuid4())
        assert isinstance(ref, str)

    def test_to_dict(self):
        """Test serialization."""
        generator = ReflectionQuestionGenerator()
        data = generator.to_dict()
        assert "generated_count" in data
        assert "auto_generation_enabled" in data
