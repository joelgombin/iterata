import pytest
import tempfile
import shutil
import json
from pathlib import Path
from iterata import CorrectionLogger, SkillGenerator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger_with_patterns(temp_dir):
    """Create a logger with enough corrections to generate patterns"""
    logger = CorrectionLogger(base_path=temp_dir)

    # Add decimal format errors (12 corrections)
    for i in range(12):
        corr = logger.log(
            original=f"1.{i:03d},50",
            corrected=f"1{i:03d}.50",
            document_id=f"invoice_{i:04d}.pdf",
            field_path="invoice.amount",
            confidence_before=0.80,
            corrector_id="analyst",
        )
        logger.explain_pending(corr.correction_id, explanation_text="Format décimal incorrect")

    # Add date format errors (8 corrections)
    for i in range(8):
        corr = logger.log(
            original=f"{i+1:02d}/01/2024",
            corrected=f"2024-01-{i+1:02d}",
            document_id=f"invoice_{100+i:04d}.pdf",
            field_path="invoice.date",
            confidence_before=0.75,
            corrector_id="analyst",
        )
        logger.explain_pending(corr.correction_id, explanation_text="Format de date ISO 8601")

    # Add vendor name errors (6 corrections)
    for i in range(6):
        corr = logger.log(
            original=f"ACME{i}",
            corrected=f"ACME Corporation {i}",
            document_id=f"invoice_{200+i:04d}.pdf",
            field_path="invoice.vendor",
            confidence_before=0.70,
            corrector_id="analyst",
        )
        logger.explain_pending(
            corr.correction_id, explanation_text="Nom complet requis (règle métier)"
        )

    return logger


class TestSkillGenerator:
    def test_init(self, temp_dir):
        """Test skill generator initialization"""
        logger = CorrectionLogger(base_path=temp_dir)
        generator = SkillGenerator(logger.storage)

        assert generator.storage is not None
        assert generator.pattern_detector is not None

    def test_can_generate_skill_not_enough_data(self, temp_dir):
        """Test can_generate_skill with insufficient data"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add only 5 corrections (less than min_corrections=10)
        for i in range(5):
            corr = logger.log(
                original=f"test{i}",
                corrected=f"fixed{i}",
                document_id=f"doc_{i}",
                field_path="field",
            )
            logger.explain_pending(corr.correction_id, explanation_text="Test")

        generator = SkillGenerator(logger.storage)
        result = generator.can_generate_skill(min_corrections=10)

        assert result["ready"] is False
        assert result["corrections_count"] == 5
        assert "Need 5 more corrections" in result["reason"]

    def test_can_generate_skill_ready(self, logger_with_patterns):
        """Test can_generate_skill with sufficient data"""
        generator = SkillGenerator(logger_with_patterns.storage)
        result = generator.can_generate_skill(min_corrections=10)

        assert result["ready"] is True
        assert result["corrections_count"] >= 10
        assert result["patterns_count"] > 0
        assert "Ready to generate skill" in result["reason"]

    def test_generate_skill_insufficient_corrections(self, temp_dir):
        """Test that generate_skill raises error with insufficient corrections"""
        logger = CorrectionLogger(base_path=temp_dir)

        # Add only 5 corrections
        for i in range(5):
            corr = logger.log(
                original=f"test{i}", corrected=f"fixed{i}", document_id=f"doc_{i}"
            )
            logger.explain_pending(corr.correction_id, explanation_text="Test")

        generator = SkillGenerator(logger.storage)

        with pytest.raises(ValueError, match="Pas assez de corrections"):
            generator.generate_skill(skill_path=f"{temp_dir}/skill")

    def test_generate_skill_creates_structure(self, logger_with_patterns, temp_dir):
        """Test that generate_skill creates the correct directory structure"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        skill_file = generator.generate_skill(
            skill_path=skill_path, skill_name="test-skill", min_corrections=10
        )

        # Check main file exists
        assert skill_file.exists()
        assert skill_file.name == "SKILL.md"

        # Check directory structure
        skill_dir = Path(skill_path)
        assert (skill_dir / "rules").exists()
        assert (skill_dir / "examples").exists()
        assert (skill_dir / "scripts").exists()

        # Check files exist
        assert (skill_dir / "README.md").exists()
        assert (skill_dir / "examples" / "corrections.json").exists()
        assert (skill_dir / "examples" / "patterns.json").exists()
        assert (skill_dir / "scripts" / "validate_extraction.py").exists()

    def test_generate_skill_md_content(self, logger_with_patterns, temp_dir):
        """Test that SKILL.md has correct content"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        skill_file = generator.generate_skill(
            skill_path=skill_path, skill_name="extraction-expertise", min_corrections=10
        )

        content = skill_file.read_text(encoding="utf-8")

        # Check for key sections
        assert "name: extraction-expertise" in content
        assert "When to use this skill" in content
        assert "Top recurring patterns" in content or "Overview" in content
        assert "Validation workflow" in content
        assert "Reference materials" in content

    def test_generate_rules_files(self, logger_with_patterns, temp_dir):
        """Test that rule files are generated"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        generator.generate_skill(skill_path=skill_path, min_corrections=10)

        rules_dir = Path(skill_path) / "rules"

        # Should have at least one rule file
        rule_files = list(rules_dir.glob("*.md"))
        assert len(rule_files) > 0

        # Check rule file content
        for rule_file in rule_files:
            content = rule_file.read_text(encoding="utf-8")
            assert "Rules" in content
            assert "Category" in content or "category" in content

    def test_generate_examples_json(self, logger_with_patterns, temp_dir):
        """Test that example JSON files are correct"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        generator.generate_skill(skill_path=skill_path, min_corrections=10)

        # Check corrections.json
        corrections_file = Path(skill_path) / "examples" / "corrections.json"
        with open(corrections_file) as f:
            corrections = json.load(f)

        assert isinstance(corrections, list)
        assert len(corrections) > 0
        assert "field" in corrections[0]
        assert "original" in corrections[0]
        assert "corrected" in corrections[0]

        # Check patterns.json
        patterns_file = Path(skill_path) / "examples" / "patterns.json"
        with open(patterns_file) as f:
            patterns = json.load(f)

        assert isinstance(patterns, dict)

    def test_generate_validation_script(self, logger_with_patterns, temp_dir):
        """Test that validation script is generated and executable"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        generator.generate_skill(skill_path=skill_path, min_corrections=10)

        script_file = Path(skill_path) / "scripts" / "validate_extraction.py"

        assert script_file.exists()

        content = script_file.read_text(encoding="utf-8")
        assert "def validate_extraction" in content
        assert "def main" in content
        assert "normalize_decimal_separator" in content

        # Check it's executable
        import stat

        assert script_file.stat().st_mode & stat.S_IXUSR

    def test_generate_readme(self, logger_with_patterns, temp_dir):
        """Test that README is generated correctly"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        generator.generate_skill(
            skill_path=skill_path, skill_name="my-extraction-skill", min_corrections=10
        )

        readme_file = Path(skill_path) / "README.md"
        assert readme_file.exists()

        content = readme_file.read_text(encoding="utf-8")
        assert "My Extraction Skill" in content
        assert "Overview" in content
        assert "Usage" in content
        assert "Contents" in content

    def test_skill_name_in_files(self, logger_with_patterns, temp_dir):
        """Test that skill name appears correctly in generated files"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"
        skill_name = "custom-extraction-skill"

        generator.generate_skill(
            skill_path=skill_path, skill_name=skill_name, min_corrections=10
        )

        skill_file = Path(skill_path) / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        assert f"name: {skill_name}" in content

    def test_pattern_count_in_skill(self, logger_with_patterns, temp_dir):
        """Test that pattern information is included in skill"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        generator.generate_skill(skill_path=skill_path, min_corrections=10)

        skill_file = Path(skill_path) / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        # Should mention patterns
        assert "pattern" in content.lower()

    def test_min_pattern_occurrences(self, logger_with_patterns, temp_dir):
        """Test that min_pattern_occurrences parameter works"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        # Generate with high threshold
        generator.generate_skill(
            skill_path=skill_path, min_corrections=10, min_pattern_occurrences=15
        )

        # Should still generate (but might have fewer patterns)
        assert (Path(skill_path) / "SKILL.md").exists()

    def test_correction_count_accurate(self, logger_with_patterns, temp_dir):
        """Test that correction counts in skill are accurate"""
        generator = SkillGenerator(logger_with_patterns.storage)
        skill_path = f"{temp_dir}/test_skill"

        corrections = logger_with_patterns.storage.load_corrections(status="explained")
        total_corrections = len(corrections)

        generator.generate_skill(skill_path=skill_path, min_corrections=10)

        skill_file = Path(skill_path) / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        # Should mention the correct number of corrections
        assert str(total_corrections) in content

    def test_multiple_skill_generation(self, logger_with_patterns, temp_dir):
        """Test generating multiple skills from same data"""
        generator = SkillGenerator(logger_with_patterns.storage)

        skill_path_1 = f"{temp_dir}/skill1"
        skill_path_2 = f"{temp_dir}/skill2"

        # Generate first skill
        generator.generate_skill(skill_path=skill_path_1, skill_name="skill-one")

        # Generate second skill
        generator.generate_skill(skill_path=skill_path_2, skill_name="skill-two")

        # Both should exist
        assert (Path(skill_path_1) / "SKILL.md").exists()
        assert (Path(skill_path_2) / "SKILL.md").exists()

        # Content should be different (different names)
        content1 = (Path(skill_path_1) / "SKILL.md").read_text()
        content2 = (Path(skill_path_2) / "SKILL.md").read_text()

        assert "skill-one" in content1
        assert "skill-two" in content2

    def test_impact_score_helper(self, temp_dir):
        """Test the _impact_score helper method"""
        logger = CorrectionLogger(base_path=temp_dir)
        generator = SkillGenerator(logger.storage)

        assert generator._impact_score("high") == 3
        assert generator._impact_score("medium") == 2
        assert generator._impact_score("low") == 1
        assert generator._impact_score("unknown") == 0
