import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from iterata import CorrectionLoop
from iterata.backends.mock import MockExplainer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def config_file(temp_dir):
    """Create a test config file"""
    config_path = Path(temp_dir) / "test_config.yaml"
    config = {
        "base_path": str(Path(temp_dir) / "corrections"),
        "skill_path": str(Path(temp_dir) / "skill"),
        "auto_explain": False,
        "min_corrections_for_skill": 5,
    }
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return str(config_path)


class TestCorrectionLoop:
    def test_init(self, temp_dir):
        """Test CorrectionLoop initialization"""
        loop = CorrectionLoop(base_path=temp_dir)

        assert loop.base_path.exists()
        assert loop.logger is not None
        assert loop.storage is not None
        assert loop.skill_generator is not None
        assert loop.stats is not None

    def test_init_with_skill_path(self, temp_dir):
        """Test initialization with skill path"""
        skill_path = str(Path(temp_dir) / "skill")
        loop = CorrectionLoop(base_path=temp_dir, skill_path=skill_path)

        assert loop.skill_path == Path(skill_path)

    def test_init_with_explainer(self, temp_dir):
        """Test initialization with explainer"""
        explainer = MockExplainer()
        loop = CorrectionLoop(
            base_path=temp_dir, explainer=explainer, auto_explain=True
        )

        assert loop.logger.explainer is not None
        assert loop.logger.auto_explain is True

    def test_from_config(self, config_file):
        """Test loading from config file"""
        loop = CorrectionLoop.from_config(config_file)

        assert loop.base_path.exists()
        assert loop.skill_path is not None
        assert loop.min_corrections_for_skill == 5

    def test_from_config_missing_file(self):
        """Test loading from non-existent config file"""
        with pytest.raises(FileNotFoundError):
            CorrectionLoop.from_config("nonexistent.yaml")

    def test_log(self, temp_dir):
        """Test logging a correction"""
        loop = CorrectionLoop(base_path=temp_dir)

        correction = loop.log(
            original="test",
            corrected="fixed",
            document_id="doc_001.pdf",
            field_path="field",
        )

        assert correction.correction_id is not None
        assert correction.original_value == "test"
        assert correction.corrected_value == "fixed"

    def test_log_with_auto_explain(self, temp_dir):
        """Test logging with auto-explain"""
        explainer = MockExplainer()
        loop = CorrectionLoop(
            base_path=temp_dir, explainer=explainer, auto_explain=True
        )

        correction = loop.log(
            original="test", corrected="fixed", document_id="doc_001.pdf"
        )

        # Should be automatically explained
        corrections = loop.storage.load_corrections(status="explained")
        assert len(corrections) == 1

    def test_get_stats(self, temp_dir):
        """Test getting statistics"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add some corrections
        for i in range(5):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        stats = loop.get_stats()

        assert stats["total_corrections"] == 5
        assert stats["corrections_explained"] == 5
        assert "patterns_count" in stats

    def test_get_detailed_stats(self, temp_dir):
        """Test getting detailed statistics"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add corrections
        for i in range(3):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        detailed_stats = loop.get_detailed_stats()

        assert "total_corrections" in detailed_stats
        assert "field_patterns" in detailed_stats
        assert "corrector_stats" in detailed_stats
        assert "confidence_stats" in detailed_stats

    def test_get_summary(self, temp_dir):
        """Test getting summary text"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add corrections
        for i in range(3):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        summary = loop.get_summary()

        assert isinstance(summary, str)
        assert "Total Corrections" in summary

    def test_get_recommendations(self, temp_dir):
        """Test getting recommendations"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add corrections
        for i in range(5):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        recommendations = loop.get_recommendations()

        assert isinstance(recommendations, list)

    def test_check_skill_readiness_not_ready(self, temp_dir):
        """Test skill readiness check when not ready"""
        loop = CorrectionLoop(base_path=temp_dir, min_corrections_for_skill=10)

        # Add only 5 corrections
        for i in range(5):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        readiness = loop.check_skill_readiness()

        assert readiness["ready"] is False
        assert readiness["corrections_count"] == 5
        assert readiness["min_required"] == 10
        assert "reason" in readiness

    def test_check_skill_readiness_ready(self, temp_dir):
        """Test skill readiness check when ready"""
        loop = CorrectionLoop(base_path=temp_dir, min_corrections_for_skill=5)

        # Add 10 corrections
        for i in range(10):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        readiness = loop.check_skill_readiness()

        assert readiness["ready"] is True
        assert readiness["corrections_count"] == 10
        assert readiness["patterns_count"] >= 0

    def test_update_skill_not_ready(self, temp_dir):
        """Test skill update when not ready"""
        skill_path = str(Path(temp_dir) / "skill")
        loop = CorrectionLoop(
            base_path=temp_dir, skill_path=skill_path, min_corrections_for_skill=10
        )

        # Add only 3 corrections
        for i in range(3):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        result = loop.update_skill()

        assert result["updated"] is False
        assert "reason" in result

    def test_update_skill_ready(self, temp_dir):
        """Test skill update when ready"""
        skill_path = str(Path(temp_dir) / "skill")
        loop = CorrectionLoop(
            base_path=temp_dir, skill_path=skill_path, min_corrections_for_skill=5
        )

        # Add 10 corrections
        for i in range(10):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        result = loop.update_skill(skill_name="test-skill")

        assert result["updated"] is True
        assert "skill_file" in result
        assert result["total_corrections"] == 10
        assert Path(result["skill_file"]).exists()

    def test_update_skill_force(self, temp_dir):
        """Test skill update with force flag"""
        skill_path = str(Path(temp_dir) / "skill")
        loop = CorrectionLoop(
            base_path=temp_dir, skill_path=skill_path, min_corrections_for_skill=20
        )

        # Add only 5 corrections
        for i in range(5):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        # Should fail without force
        result = loop.update_skill()
        assert result["updated"] is False

        # Should succeed with force
        result = loop.update_skill(force=True)
        assert result["updated"] is True

    def test_export_stats_json(self, temp_dir):
        """Test JSON export"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add corrections
        for i in range(3):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        json_export = loop.export_stats_json()

        assert isinstance(json_export, str)
        assert len(json_export) > 0

        import json

        data = json.loads(json_export)
        assert data["total_corrections"] == 3

    def test_export_stats_csv(self, temp_dir):
        """Test CSV export"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add corrections
        for i in range(3):
            corr = loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id=f"doc_{i}.pdf",
            )
            loop.logger.explain_pending(corr.correction_id, explanation_text="Test")

        csv_export = loop.export_stats_csv()

        assert isinstance(csv_export, str)
        assert len(csv_export) > 0

        lines = csv_export.strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 row

    def test_config_with_backend(self, temp_dir):
        """Test config file with backend configuration"""
        config_path = Path(temp_dir) / "test_config.yaml"
        config = {
            "base_path": str(Path(temp_dir) / "corrections"),
            "skill_path": str(Path(temp_dir) / "skill"),
            "auto_explain": True,
            "min_corrections_for_skill": 5,
            "backend": {"provider": "mock", "custom_param": "test"},
        }
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        # Should not fail with unknown backend provider (uses mock)
        loop = CorrectionLoop.from_config(str(config_path))
        assert loop is not None

    def test_multiple_corrections_same_document(self, temp_dir):
        """Test logging multiple corrections for the same document"""
        loop = CorrectionLoop(base_path=temp_dir)

        # Add multiple corrections for same document
        for i in range(3):
            loop.log(
                original=f"test_{i}",
                corrected=f"fixed_{i}",
                document_id="doc_001.pdf",
                field_path=f"field_{i}",
            )

        stats = loop.get_stats()
        assert stats["total_corrections"] == 3

    def test_context_preservation(self, temp_dir):
        """Test that context is preserved in corrections"""
        loop = CorrectionLoop(base_path=temp_dir)

        context = {"model": "gpt-4", "temperature": 0.5, "custom_data": {"key": "value"}}

        correction = loop.log(
            original="test",
            corrected="fixed",
            document_id="doc_001.pdf",
            context=context,
        )

        # Reload and check context
        corrections = loop.storage.load_corrections()
        assert len(corrections) == 1
        assert corrections[0].context["model"] == "gpt-4"
        assert corrections[0].context["custom_data"]["key"] == "value"
