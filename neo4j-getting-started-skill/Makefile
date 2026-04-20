SKILL_NAME := neo4j-getting-started-skill
SKILL_INSTALL_DIR := $(HOME)/.claude/skills/$(SKILL_NAME)
SKILL_SRC := $(CURDIR)

HARNESS := tests/harness/runner.py
PERSONAS_DIR := tests/personas

# Repo root (one level up from neo4j-getting-started-skill/neo4j-getting-started-skill/)
REPO_ROOT := $(CURDIR)/..

.PHONY: install-skill uninstall-skill reinstall-skill \
        test-cypher test-load \
        integration-alex integration-sam integration-priya integration-elena \
        integration-alex-from-explore \
        test-quick manual help

help:
	@echo "Neo4j Getting-Started Skill"
	@echo ""
	@echo "Skill management:"
	@echo "  make install-skill    Install skill to ~/.claude/skills/"
	@echo "  make uninstall-skill  Remove skill from ~/.claude/skills/"
	@echo "  make reinstall-skill  Uninstall + install (pick up changes)"
	@echo ""
	@echo "Cypher & load validation (requires localhost:7687, db=jtbd):"
	@echo "  make test-cypher      Validate all Cypher blocks in references/"
	@echo "  make test-load        Validate Python load scripts"
	@echo ""
	@echo "Integration tests (installs skill, runs Claude, validates gates):"
	@echo "  make integration-alex    Persona: Alex (beginner, social, notebook)"
	@echo "  make integration-sam     Persona: Sam (developer, e-commerce, FastAPI)"
	@echo "  make integration-priya   Persona: Priya (compliance analyst, fintech fraud rings, Streamlit)"
	@echo "  make integration-elena   Persona: Elena (clinical informatics, patient journey, Docker, notebook)"
	@echo ""
	@echo "Other:"
	@echo "  make test-quick    Validate skill file structure (no Claude)"
	@echo "  make manual        Print manual testing instructions"
	@echo ""

# ─── Skill installation ───────────────────────────────────────────────────────

install-skill:
	@echo "Installing skill to $(SKILL_INSTALL_DIR) ..."
	@mkdir -p "$(SKILL_INSTALL_DIR)"
	@cp -R "$(SKILL_SRC)/." "$(SKILL_INSTALL_DIR)/"
	@echo "  ✓ Installed: $(SKILL_INSTALL_DIR)"
	@echo "  Trigger with: /$(SKILL_NAME)"

uninstall-skill:
	@if [ -d "$(SKILL_INSTALL_DIR)" ]; then \
	  rm -rf "$(SKILL_INSTALL_DIR)"; \
	  echo "  ✓ Removed: $(SKILL_INSTALL_DIR)"; \
	else \
	  echo "  (not installed — nothing to remove)"; \
	fi

reinstall-skill: uninstall-skill install-skill

# ─── Cypher & load validation ─────────────────────────────────────────────────

test-cypher:
	@echo "Validating Cypher blocks in references/ ..."
	cd "$(REPO_ROOT)" && python3 validate_cypher.py


test-load:
	@echo "Validating Python load scripts ..."
	cd "$(REPO_ROOT)" && python3 test_load_scripts.py

# ─── Integration tests ────────────────────────────────────────────────────────

integration-alex: reinstall-skill
	@echo "Running integration test: alex_beginner ..."
	python3 $(HARNESS) --persona $(PERSONAS_DIR)/alex_beginner.yml --verbose
	@$(MAKE) --no-print-directory uninstall-skill

integration-sam: reinstall-skill
	@echo "Running integration test: sam_developer ..."
	python3 $(HARNESS) --persona $(PERSONAS_DIR)/sam_developer.yml \
	  --fixture $(CURDIR)/tests/fixtures/sam_ecommerce --verbose
	@$(MAKE) --no-print-directory uninstall-skill

integration-priya: reinstall-skill
	@echo "Running integration test: priya_analyst ..."
	python3 $(HARNESS) --persona $(PERSONAS_DIR)/priya_analyst.yml --verbose
	@$(MAKE) --no-print-directory uninstall-skill

integration-elena: reinstall-skill
	@echo "Running integration test: elena_healthcare ..."
	@echo "(Requires Docker — runner starts/stops neo4j-elena-test container)"
	python3 $(HARNESS) --persona $(PERSONAS_DIR)/elena_healthcare.yml --verbose
	@$(MAKE) --no-print-directory uninstall-skill

integration-alex-from-explore: reinstall-skill
	@echo "Running integration test: alex_beginner starting from stage 5-explore ..."
	@echo "(Stages 0-4 pre-populated from fixture)"
	python3 $(HARNESS) --persona $(PERSONAS_DIR)/alex_beginner.yml \
	  --fixture $(CURDIR)/tests/fixtures/alex_after_load --verbose
	@$(MAKE) --no-print-directory uninstall-skill

# ─── Structure validation (no Claude) ─────────────────────────────────────────

test-quick:
	@echo "Validating skill structure..."
	@test -f SKILL.md && echo "  ✓ SKILL.md" || echo "  ✗ SKILL.md MISSING"
	@test -f AGENTS.md && echo "  ✓ AGENTS.md" || echo "  ✗ AGENTS.md MISSING"
	@for stage in 0-prerequisites 1-context 2-provision 3-model 4-load 5-explore 6-query 7-build; do \
	  test -f references/$$stage.md \
	    && echo "  ✓ references/$$stage.md" \
	    || echo "  ✗ references/$$stage.md MISSING"; \
	done
	@test -f references/domain-patterns.md && echo "  ✓ domain-patterns.md" || echo "  ✗ domain-patterns.md MISSING"
	@test -f references/capabilities/execute-cypher.md && echo "  ✓ execute-cypher.md" || echo "  ✗ execute-cypher.md MISSING"
	@test -f references/capabilities/cypher-authoring.md && echo "  ✓ cypher-authoring.md" || echo "  ✗ cypher-authoring.md MISSING"
	@test -f references/capabilities/mcp-config.md && echo "  ✓ mcp-config.md" || echo "  ✗ mcp-config.md MISSING"
	@test -f tests/personas/alex_beginner.yml && echo "  ✓ alex_beginner.yml" || echo "  ✗ alex_beginner.yml MISSING"
	@test -f tests/personas/sam_developer.yml && echo "  ✓ sam_developer.yml" || echo "  ✗ sam_developer.yml MISSING"
	@test -f tests/personas/priya_analyst.yml && echo "  ✓ priya_analyst.yml" || echo "  ✗ priya_analyst.yml MISSING"
	@test -f tests/personas/elena_healthcare.yml && echo "  ✓ elena_healthcare.yml" || echo "  ✗ elena_healthcare.yml MISSING"
	@test -f tests/harness/runner.py && echo "  ✓ runner.py" || echo "  ✗ runner.py MISSING"
	@test -f tests/harness/validator.py && echo "  ✓ validator.py" || echo "  ✗ validator.py MISSING"
	@test -f scripts/validate_queries.py && echo "  ✓ scripts/validate_queries.py" || echo "  ✗ scripts/validate_queries.py MISSING"
	@python3 -m py_compile tests/harness/runner.py && echo "  ✓ runner.py syntax OK" || echo "  ✗ runner.py syntax ERRORS"
	@python3 -m py_compile tests/harness/validator.py && echo "  ✓ validator.py syntax OK" || echo "  ✗ validator.py syntax ERRORS"
	@python3 -m py_compile scripts/validate_queries.py && echo "  ✓ validate_queries.py syntax OK" || echo "  ✗ validate_queries.py syntax ERRORS"
	@echo "Done."

# ─── Manual testing ───────────────────────────────────────────────────────────

manual:
	@echo "Manual testing — install the skill first:"
	@echo ""
	@echo "  make install-skill"
	@echo ""
	@echo "Then start Claude Code in a new empty directory:"
	@echo "  mkdir /tmp/neo4j-test && cd /tmp/neo4j-test && claude"
	@echo ""
	@echo "Trigger the skill with:"
	@echo "  /$(SKILL_NAME)"
	@echo ""
	@echo "Or paste a full context prompt for Persona 1 (Alex):"
	@echo "  /$(SKILL_NAME) I want to get started with Neo4j."
	@echo "  Domain: social network, use-case: friend recommendations,"
	@echo "  I am a beginner, use Aura Free, synthetic data, Python notebook."
	@echo ""
	@echo "For Persona 2 (Sam):"
	@echo "  /$(SKILL_NAME) I have an e-commerce project with CSV files."
	@echo "  Domain: e-commerce, use-case: product recommendations,"
	@echo "  experience: intermediate Python+SQL developer,"
	@echo "  Aura Pro on AWS, import CSVs, build FastAPI backend with MCP."
	@echo ""
	@echo "Target: ≤15 min autonomous, ≤90 min HITL"
	@echo ""
	@echo "After testing:"
	@echo "  make uninstall-skill"
