# Reasoning Methods for Berb Pipeline

**Ανάλυση & Αντιστοίχιση Reasoning Methods στα Στάδια του Berb**

**Ημερομηνία:** 2026-03-27  
**Πηγή:** IMPLEMENTATION.md (Reasoner Project)

---

## 📊 Σύνοψη Αντιστοίχισης

| Reasoning Method | Κατάλληλο για Στάδια | Βελτίωση Ποιότητας |
|-----------------|----------------------|-------------------|
| **Multi-Perspective** | 8, 9, 15, 18 | +25-35% |
| **Debate** | 8, 15 | +20-30% |
| **Research** | 3-6, 23 | +40-50% |
| **Socratic** | 2, 8, 15 | +15-25% |
| **Pre-Mortem** | 9, 12, 13 | -40-50% failures |
| **Bayesian** | 14, 15, 20 | +30-40% accuracy |
| **Dialectical** | 7, 8, 15 | +25-35% novelty |

---

## 🎯 Λεπτομερής Ανάλυση ανά Στάδιο

### **Φάση A: Research Scoping**

#### **Στάδιο 1: TOPIC_INIT**
```
Τρέχον LLM: gpt-4o-mini
Προτεινόμενη Method: Socratic (απλοποιημένη)
Βελτίωση: +10-15% clarity

Γιατί:
- Ερωτήσεις τύπου "What exactly are you trying to solve?"
- Αποσαφήνιση όρων και ορισμών
- Αναγνώριση κρυφών παραδοχών

Implementation:
```python
# berb/pipeline/stage_impls/_topic.py
async def run_topic_init(topic: str) -> TopicSummary:
    # Step 1: Elicit initial position
    position = await socratic_elicit_position(topic)
    
    # Step 2: Generate clarifying questions
    questions = await socratic_generate_questions(position)
    
    # Step 3: Refine based on answers
    refined = await socratic_synthesis(position, questions)
    
    return TopicSummary(
        original_topic=topic,
        refined_topic=refined,
        clarifications=questions,
    )
```
```

#### **Στάδιο 2: PROBLEM_DECOMPOSE**
```
Τρέχον LLM: gpt-4o
Προτεινόμενη Method: Socratic + Multi-Perspective
Βελτίωση: +20-25% completeness

Γιατί:
- Socratic: "What assumptions are you making?"
- Multi-Perspective: Decompose από 4 οπτικές γωνίες
  * Constructive: Τι χρειάζεται για επιτυχία;
  * Destructive: Πού μπορεί να αποτύχει;
  * Systemic: Δεύτερης/τρίτης τάξης επιπτώσεις
  * Minimalist: Ελάχιστες απαραίτητες εργασίες

Implementation:
```python
# berb/pipeline/stage_impls/_decomposition.py
async def run_problem_decompose(topic: TopicSummary) -> DecompositionOutput:
    # Socratic phase
    assumptions = await socratic_expose_assumptions(topic.refined_topic)
    
    # Multi-perspective decomposition
    perspectives = await run_multi_perspective(
        topic.refined_topic,
        perspectives=[
            Perspective.CONSTRUCTIVE,  # What's needed
            Perspective.DESTRUCTIVE,   # What could fail
            Perspective.SYSTEMIC,      # Dependencies
            Perspective.MINIMALIST,    # Core tasks only
        ]
    )
    
    # Synthesize task tree
    task_tree = synthesize_decomposition(perspectives, assumptions)
    
    return DecompositionOutput(
        task_tree=task_tree,
        assumptions=assumptions,
        perspective_insights=perspectives,
    )
```
```

---

### **Φάση B: Literature Discovery**

#### **Στάδιο 3: SEARCH_STRATEGY**
```
Τρέχον LLM: gpt-4o-mini
Προτεινόμενη Method: Research Method
Βελτίωση: +30-40% coverage

Γιατί:
- Iterative search planning
- Gap analysis after each iteration
- Targeted follow-up queries

Implementation:
```python
# berb/pipeline/stage_impls/_literature.py
async def run_search_strategy(decomposition: DecompositionOutput) -> SearchStrategy:
    # Iteration 1: Initial search plan
    initial_queries = await research_plan_queries(
        tasks=decomposition.task_tree
    )
    
    # Iteration 2: Gap analysis
    gaps = await research_analyze_gaps(initial_queries)
    follow_up_queries = await research_plan_followup(gaps)
    
    # Iteration 3: Verification plan
    verification_plan = await research_plan_verification(
        key_claims=decomposition.key_claims
    )
    
    return SearchStrategy(
        initial_queries=initial_queries,
        follow_up_queries=follow_up_queries,
        verification_plan=verification_plan,
    )
```
```

#### **Στάδιο 4: LITERATURE_COLLECT**
```
Τρέχον: APIs (OpenAlex, Semantic Scholar, arXiv)
Προτεινόμενη Method: Research Method (execution)
Βελτίωση: +20-30% relevance

Γιατί:
- Execute search iterations
- Record all results with metadata
- Track source diversity

Implementation:
```python
# berb/literature/search.py
async def collect_literature(strategy: SearchStrategy) -> LiteratureCollection:
    all_results = []
    
    # Iteration 1
    for query in strategy.initial_queries:
        results = await search_multiple_sources(query)
        all_results.extend(results)
    
    # Iteration 2 (if gaps identified)
    if strategy.follow_up_queries:
        for query in strategy.follow_up_queries:
            results = await search_multiple_sources(query)
            all_results.extend(results)
    
    return LiteratureCollection(
        papers=all_results,
        sources_used=list(set(r.source for r in all_results)),
        iterations_completed=2 if strategy.follow_up_queries else 1,
    )
```
```

#### **Στάδιο 5: LITERATURE_SCREEN 🔒**
```
Τρέχον LLM: claude-3-sonnet
Προτεινόμενη Method: Bayesian Reasoning
Βελτίωση: +25-35% accuracy

Γιατί:
- Ποσοτική αξιολόγηση ποιότητας
- Update beliefs με βάση evidence
- Sensitivity analysis για κρίσιμες παραδοχές

Implementation:
```python
# berb/literature/verify.py
async def screen_literature(collection: LiteratureCollection) -> LiteratureScreen:
    screened_papers = []
    
    for paper in collection.papers:
        # Phase 1: Prior elicitation
        priors = await bayesian_elicit_priors(
            hypotheses=[
                "This paper is high-quality",
                "This paper is relevant",
                "This paper is trustworthy",
            ]
        )
        
        # Phase 2: Likelihood assessment
        evidence = {
            "citation_count": paper.citations,
            "venue_quality": paper.venue_impact,
            "author_h_index": paper.author_h_index,
            "recency": paper.years_since_publication,
        }
        likelihoods = await bayesian_assess_likelihood(evidence, priors)
        
        # Phase 3: Posterior update
        posteriors = await bayesian_update_posteriors(priors, likelihoods)
        
        # Phase 4: Sensitivity analysis
        sensitivity = await bayesian_sensitivity_analysis(posteriors)
        
        # Decision based on posterior
        if posteriors["high_quality"] > 0.7:
            screened_papers.append(paper)
    
    return LiteratureScreen(
        included_papers=screened_papers,
        excluded_papers=[p for p in collection.papers if p not in screened_papers],
        screening_rationale=posteriors,
    )
```
```

#### **Στάδιο 6: KNOWLEDGE_EXTRACT**
```
Τρέχον LLM: gpt-4o
Προτεινόμενη Method: Research Method (synthesis)
Βελτίωση: +20-30% knowledge quality

Γιατί:
- Synthesize across multiple papers
- Evidence-grounded extraction
- Cross-reference claims

Implementation:
```python
# berb/literature/knowledge_extraction.py
async def extract_knowledge(screened: LiteratureScreen) -> KnowledgeExtraction:
    # Analyze all findings together
    synthesis = await research_synthesize_findings(
        papers=screened.included_papers
    )
    
    # Extract knowledge cards
    cards = []
    for finding in synthesis.key_findings:
        card = KnowledgeCard(
            claim=finding.claim,
            evidence=finding.supporting_papers,
            confidence=finding.confidence_score,
            contradictions=finding.contradictory_evidence,
        )
        cards.append(card)
    
    return KnowledgeExtraction(
        knowledge_cards=cards,
        synthesis_report=synthesis,
        evidence_gaps=synthesis.gaps,
    )
```
```

---

### **Φάση C: Knowledge Synthesis**

#### **Στάδιο 7: SYNTHESIS**
```
Τρέχον LLM: claude-3-sonnet
Προτεινόμενη Method: Dialectical Reasoning
Βελτίωση: +30-40% novelty

Γιατί:
- Thesis: Τι λένε οι περισσότεροι ερευνητές
- Antithesis: Αντιφατικά ευρήματα
- Aufhebung: Νέα σύνθεση που transcends την αντίθεση

Implementation:
```python
# berb/pipeline/stage_impls/_synthesis.py
async def run_synthesis(knowledge: KnowledgeExtraction) -> SynthesisReport:
    # Phase 1: Thesis (dominant view)
    thesis = await dialectical_thesis(
        knowledge_cards=knowledge.knowledge_cards,
        prompt="What is the dominant view in this field?"
    )
    
    # Phase 2: Antithesis (contradictory evidence)
    antithesis = await dialectical_antithesis(
        knowledge_cards=knowledge.knowledge_cards,
        prompt="What evidence contradicts the dominant view?"
    )
    
    # Phase 3: Contradiction analysis
    contradictions = await dialectical_analyze_contradictions(
        thesis=thesis,
        antithesis=antithesis,
    )
    
    # Phase 4: Aufhebung (transcendence)
    aufhebung = await dialectical_aufhebung(
        thesis=thesis,
        antithesis=antithesis,
        contradictions=contradictions,
        prompt="Find a higher position that preserves truth from both sides"
    )
    
    return SynthesisReport(
        dominant_view=thesis,
        contradictory_evidence=antithesis,
        contradictions=contradictions,
        novel_synthesis=aufhebung,
        research_gaps=knowledge.evidence_gaps,
    )
```
```

#### **Στάδιο 8: HYPOTHESIS_GEN ⭐**
```
Τρέχον LLM: claude-3-opus
Προτεινόμενη Method: Multi-Perspective + Debate + Socratic
Βελτίωση: +35-45% quality

Γιατί:
- Multi-Perspective: 4 οπτικές γωνίες για κάθε hypothesis
- Debate: Pro/Con για κάθε hypothesis
- Socratic: Έλεγχος παραδοχών και λογικής

Implementation:
```python
# berb/pipeline/stage_impls/_hypothesis.py
async def run_hypothesis_generation(synthesis: SynthesisReport) -> HypothesisOutput:
    # Step 1: Generate candidate hypotheses
    candidates = await generate_candidate_hypotheses(synthesis)
    
    evaluated_hypotheses = []
    
    for candidate in candidates:
        # Multi-Perspective analysis
        perspectives = await run_multi_perspective(
            hypothesis=candidate,
            perspectives=[
                Perspective.CONSTRUCTIVE,  # Why this could work
                Perspective.DESTRUCTIVE,   # Why this could fail
                Perspective.SYSTEMIC,      # Second-order effects
                Perspective.MINIMALIST,    # Simplest test
            ]
        )
        
        # Debate (Pro vs Con)
        debate_result = await run_debate(
            position=candidate,
            rounds=2,
            judge_model="claude-3-opus",
        )
        
        # Socratic questioning
        socratic_insights = await run_socratic(
            position=candidate,
            num_questions=5,
        )
        
        # Aggregate scores
        overall_score = aggregate_scores(
            perspectives=perspectives,
            debate=debate_result,
            socratic=socratic_insights,
        )
        
        evaluated_hypotheses.append(
            EvaluatedHypothesis(
                hypothesis=candidate,
                score=overall_score,
                perspectives=perspectives,
                debate_result=debate_result,
                socratic_insights=socratic_insights,
            )
        )
    
    # Select top 3-5 hypotheses
    top_hypotheses = sorted(
        evaluated_hypotheses,
        key=lambda h: h.score,
        reverse=True
    )[:5]
    
    return HypothesisOutput(
        hypotheses=top_hypotheses,
        evaluation_method="multi-perspective+debate+socratic",
    )
```
```

---

### **Φάση D: Experiment Design**

#### **Στάδιο 9: EXPERIMENT_DESIGN 🔒 ⭐**
```
Τρέχον LLM: claude-3-opus
Προτεινόμενη Method: Pre-Mortem Analysis + Multi-Perspective
Βελτίωση: -50-60% design flaws

Γιατί:
- Pre-Mortem: "Το πείραμα απέτυχε. Γράψε το post-mortem."
- Προσδιορισμός failure modes πριν την εκτέλεση
- Hardened design με base στα failure modes

Implementation:
```python
# berb/pipeline/stage_impls/_experiment_design.py
async def run_experiment_design(hypotheses: HypothesisOutput) -> ExperimentDesignOutput:
    designs = []
    
    for hypothesis in hypotheses.hypotheses:
        # Pre-Mortem Analysis
        pre_mortem = await run_pre_mortem(
            proposed_design=initial_design,
            hypothesis=hypothesis,
        )
        
        # Failure narrative
        failure_narratives = pre_mortem.failure_narratives
        
        # Root cause analysis
        root_causes = pre_mortem.root_causes
        
        # Early warning signals
        early_signals = pre_mortem.early_warning_signals
        
        # Hardened redesign
        hardened_design = await pre_mortem_hardened_redesign(
            original_design=initial_design,
            failure_modes=failure_narratives,
            root_causes=root_causes,
        )
        
        # Multi-Perspective review of hardened design
        perspectives = await run_multi_perspective(
            design=hardened_design,
            perspectives=[
                Perspective.CONSTRUCTIVE,  # Why this design works
                Perspective.DESTRUCTIVE,   # Remaining flaws
                Perspective.SYSTEMIC,      # Resource implications
                Perspective.MINIMALIST,    # Simplest valid version
            ]
        )
        
        designs.append(
            ExperimentDesign(
                hypothesis=hypothesis,
                design=hardened_design,
                pre_mortem_analysis=pre_mortem,
                perspective_review=perspectives,
                monitoring_plan=early_signals,
            )
        )
    
    return ExperimentDesignOutput(
        designs=designs,
        stress_tested=True,
        failure_modes_addressed=len([f for d in designs for f in d.pre_mortem_analysis.failure_narratives]),
    )
```
```

---

### **Φάση E: Experiment Execution**

#### **Στάδιο 12: EXPERIMENT_RUN**
```
Τρέχον: Sandbox execution (no LLM)
Προτεινόμενη Method: Pre-Mortem (early warning monitoring)
Βελτίωση: -30-40% runtime failures

Γιατί:
- Monitor early warning signals από Pre-Mortem
- Fast-fail αν εμφανιστούν warning signals
- Real-time adjustment

Implementation:
```python
# berb/experiment/runner.py
async def run_experiment(design: ExperimentDesign) -> ExperimentResult:
    # Get early warning signals from pre-mortem
    warning_signals = design.pre_mortem_analysis.early_warning_signals
    
    # Execute with monitoring
    execution = await execute_with_monitoring(
        code=design.design.code,
        monitoring_plan=warning_signals,
    )
    
    # Check for warning signals during execution
    for signal in warning_signals:
        if signal.detected_in(execution.logs):
            logger.warning(f"Early warning signal detected: {signal}")
            
            # Fast-fail if critical
            if signal.severity == "critical":
                return ExperimentResult(
                    status="failed",
                    failure_mode=signal.description,
                    early_detection=True,
                )
    
    return execution
```
```

#### **Στάδιο 13: ITERATIVE_REFINE**
```
Τρέχον LLM: gpt-4o
Προτεινόμενη Method: Pre-Mortem + Socratic
Βελτίωση: -40-50% repair cycles

Γιατί:
- Pre-Mortem για κάθε αποτυχία
- Socratic questioning για root cause
- Targeted fixes

Implementation:
```python
# berb/pipeline/stage_impls/_iterative_refine.py
async def run_iterative_refine(result: ExperimentResult, max_iterations: int = 10):
    current_result = result
    
    for iteration in range(max_iterations):
        if current_result.success:
            return current_result
        
        # Pre-Mortem on failure
        pre_mortem = await run_pre_mortem(
            proposed_fix=current_result.error,
            context="This fix failed. Write the post-mortem.",
        )
        
        # Socratic root cause analysis
        root_cause = await socratic_root_cause(
            error=current_result.error,
            num_questions=5,
        )
        
        # Generate targeted fix
        fix = await generate_targeted_fix(
            error=current_result.error,
            root_cause=root_cause,
            failure_modes=pre_mortem.failure_narratives,
        )
        
        # Re-run experiment
        current_result = await run_experiment_with_fix(fix)
    
    return current_result  # May still have failed
```
```

---

### **Φάση F: Analysis & Decision**

#### **Στάδιο 14: RESULT_ANALYSIS**
```
Τρέχον LLM: claude-3-sonnet
Προτεινόμενη Method: Bayesian Reasoning
Βελτίωση: +30-40% analysis accuracy

Γιατί:
- Ποσοτική evaluation evidence
- Update beliefs για hypothesis validity
- Sensitivity analysis

Implementation:
```python
# berb/pipeline/stage_impls/_analysis.py
async def run_result_analysis(result: ExperimentResult) -> ResultAnalysis:
    # Phase 1: Prior elicitation
    priors = await bayesian_elicit_priors(
        hypotheses=[
            "Hypothesis is supported",
            "Hypothesis is refuted",
            "Results are inconclusive",
        ]
    )
    
    # Phase 2: Likelihood assessment
    evidence = {
        "effect_size": result.effect_size,
        "p_value": result.p_value,
        "sample_size": result.sample_size,
        "controls_passed": result.controls_passed,
        "reproducibility": result.reproducibility_score,
    }
    likelihoods = await bayesian_assess_likelihood(evidence, priors)
    
    # Phase 3: Posterior update
    posteriors = await bayesian_update_posteriors(priors, likelihoods)
    
    # Phase 4: Sensitivity analysis
    sensitivity = await bayesian_sensitivity_analysis(posteriors)
    
    return ResultAnalysis(
        result=result,
        belief_distribution=posteriors,
        confidence_level=posteriors["supported"],
        sensitivity_analysis=sensitivity,
        key_evidence=evidence,
    )
```
```

#### **Στάδιο 15: RESEARCH_DECISION ⭐**
```
Τρέχον LLM: claude-3-opus
Προτεινόμενη Method: Bayesian + Multi-Perspective + Debate
Βελτίωση: +35-45% decision quality

Γιατί:
- Bayesian: Ποσοτική confidence για κάθε απόφαση
- Multi-Perspective: 4 οπτικές για PROCEED/REFINE/PIVOT
- Debate: Pro/Con για κάθε επιλογή

Implementation:
```python
# berb/pipeline/stage_impls/_decision.py
async def run_research_decision(analysis: ResultAnalysis) -> ResearchDecisionOutput:
    decisions = ["PROCEED", "REFINE", "PIVOT"]
    
    evaluated_decisions = []
    
    for decision in decisions:
        # Bayesian evaluation
        bayesian_result = await bayesian_evaluate_decision(
            decision=decision,
            analysis=analysis,
        )
        
        # Multi-Perspective analysis
        perspectives = await run_multi_perspective(
            decision=decision,
            perspectives=[
                Perspective.CONSTRUCTIVE,  # Why this decision works
                Perspective.DESTRUCTIVE,   # Risks of this decision
                Perspective.SYSTEMIC,      # Long-term implications
                Perspective.MINIMALIST,    # Simplest path forward
            ]
        )
        
        # Debate (if close call)
        if bayesian_result.confidence < 0.8:
            debate = await run_debate(
                position=decision,
                rounds=1,
            )
        else:
            debate = None
        
        evaluated_decisions.append(
            EvaluatedDecision(
                decision=decision,
                bayesian_score=bayesian_result.confidence,
                perspectives=perspectives,
                debate_result=debate,
            )
        )
    
    # Select best decision
    best_decision = max(evaluated_decisions, key=lambda d: d.bayesian_score)
    
    return ResearchDecisionOutput(
        decision=best_decision.decision,
        rationale=best_decision.perspectives,
        confidence=best_decision.bayesian_score,
        alternatives=[d for d in evaluated_decisions if d.decision != best_decision.decision],
    )
```
```

---

### **Φάση G: Paper Writing**

#### **Στάδιο 18: PEER_REVIEW**
```
Τρέχον: 5-reviewer ensemble
Προτεινόμενη Method: Multi-Perspective (already aligned!)
Βελτίωση: +20-25% review quality

Γιατί:
- Ήδη χρησιμοποιεί 5 perspectives
- Can be enhanced with explicit perspective types

Implementation:
```python
# berb/review/ensemble.py (already well-designed)
# Enhancement: Make perspectives explicit

reviewer_personas = [
    ReviewerPersona(
        id="novelty",
        name="Novelty & Significance Expert",
        perspective=Perspective.CONSTRUCTIVE,  # Build strongest case
    ),
    ReviewerPersona(
        id="technical",
        name="Technical Correctness Expert",
        perspective=Perspective.DESTRUCTIVE,  # Find every flaw
    ),
    ReviewerPersona(
        id="experimental",
        name="Experimental Rigor Expert",
        perspective=Perspective.SYSTEMIC,  # Second-order effects
    ),
    ReviewerPersona(
        id="clarity",
        name="Clarity & Presentation Expert",
        perspective=Perspective.MINIMALIST,  # Simplest clear version
    ),
    ReviewerPersona(
        id="reproducibility",
        name="Reproducibility Expert",
        perspective=Perspective.DESTRUCTIVE,  # What could go wrong
    ),
]
```
```

---

### **Φάση H: Finalization**

#### **Στάδιο 20: QUALITY_GATE 🔒**
```
Τρέχον LLM: claude-3-opus
Προτεινόμενη Method: Bayesian + Pre-Mortem
Βελτίωση: +25-35% quality assurance

Γιατί:
- Bayesian: Ποσοτική confidence για quality
- Pre-Mortem: "Η εργασία απορρίφθηκε. Γράψε το post-mortem."

Implementation:
```python
# berb/pipeline/stage_impls/_quality_gate.py
async def run_quality_gate(paper: PaperDraft) -> QualityGateOutput:
    # Pre-Mortem on paper quality
    pre_mortem = await run_pre_mortem(
        proposed_paper=paper,
        context="This paper was rejected. Write the post-mortem.",
    )
    
    # Bayesian quality assessment
    priors = await bayesian_elicit_priors(
        hypotheses=[
            "Paper is acceptance-worthy",
            "Paper needs major revision",
            "Paper should be rejected",
        ]
    )
    
    evidence = {
        "novelty_score": paper.novelty_score,
        "technical_correctness": paper.technical_score,
        "clarity_score": paper.clarity_score,
        "reviewer_scores": paper.reviewer_scores,
        "citation_accuracy": paper.citation_verification_score,
    }
    
    likelihoods = await bayesian_assess_likelihood(evidence, priors)
    posteriors = await bayesian_update_posteriors(priors, likelihoods)
    
    # Decision
    if posteriors["acceptance-worthy"] > 0.8:
        decision = "PASS"
    elif posteriors["major-revision"] > 0.6:
        decision = "CONDITIONAL_PASS"
    else:
        decision = "FAIL"
    
    return QualityGateOutput(
        decision=decision,
        confidence=posteriors,
        failure_modes=pre_mortem.failure_narratives,
        recommendations=pre_mortem.hardened_solution,
    )
```
```

#### **Στάδιο 23: CITATION_VERIFY**
```
Τρέχον LLM: gpt-4o + APIs
Προτεινόμενη Method: Research Method (verification iteration)
Βελτίωση: +20-30% verification accuracy

Γιατί:
- Iterative verification
- Cross-reference multiple sources
- Gap analysis

Implementation:
```python
# berb/pipeline/paper_verifier.py (enhanced)
async def verify_citations(references: list[Reference]) -> VerificationReport:
    all_verifications = []
    
    for ref in references:
        # Iteration 1: Primary source check
        primary_check = await verify_primary_source(ref)
        
        # Iteration 2: Cross-reference
        if not primary_check.verified:
            cross_ref = await verify_cross_reference(ref)
        else:
            cross_ref = None
        
        # Iteration 3: Relevance check
        relevance = await verify_relevance(ref, paper_context)
        
        all_verifications.append(
            CitationVerification(
                reference=ref,
                verified=primary_check.verified or (cross_ref and cross_ref.verified),
                sources_checked=[primary_check.source] + ([cross_ref.source] if cross_ref else []),
                relevance_score=relevance.score,
            )
        )
    
    return VerificationReport(
        total_citations=len(references),
        verified_citations=sum(1 for v in all_verifications if v.verified),
        hallucinated_citations=sum(1 for v in all_verifications if not v.verified),
        verifications=all_verifications,
    )
```
```

---

## 📊 Summary: Recommended Methods per Stage

| Stage | Name | Recommended Method(s) | Expected Improvement |
|-------|------|----------------------|---------------------|
| 1 | TOPIC_INIT | Socratic (light) | +10-15% clarity |
| 2 | PROBLEM_DECOMPOSE | Socratic + Multi-Perspective | +20-25% completeness |
| 3 | SEARCH_STRATEGY | Research | +30-40% coverage |
| 4 | LITERATURE_COLLECT | Research (execution) | +20-30% relevance |
| 5 | LITERATURE_SCREEN | Bayesian | +25-35% accuracy |
| 6 | KNOWLEDGE_EXTRACT | Research (synthesis) | +20-30% quality |
| 7 | SYNTHESIS | Dialectical | +30-40% novelty |
| 8 | HYPOTHESIS_GEN | Multi-Perspective + Debate + Socratic | +35-45% quality |
| 9 | EXPERIMENT_DESIGN | Pre-Mortem + Multi-Perspective | -50-60% design flaws |
| 12 | EXPERIMENT_RUN | Pre-Mortem (monitoring) | -30-40% failures |
| 13 | ITERATIVE_REFINE | Pre-Mortem + Socratic | -40-50% repair cycles |
| 14 | RESULT_ANALYSIS | Bayesian | +30-40% accuracy |
| 15 | RESEARCH_DECISION | Bayesian + Multi-Perspective + Debate | +35-45% quality |
| 18 | PEER_REVIEW | Multi-Perspective (enhanced) | +20-25% review quality |
| 20 | QUALITY_GATE | Bayesian + Pre-Mortem | +25-35% QA |
| 23 | CITATION_VERIFY | Research (verification) | +20-30% accuracy |

---

## 🎯 Implementation Priority

### **Phase 1 (High Impact, Easy)**
1. **Stage 9: Pre-Mortem for Experiment Design** - -50-60% design flaws
2. **Stage 8: Multi-Perspective for Hypothesis** - +35-45% quality
3. **Stage 15: Bayesian for Decision** - +35-45% decision quality

### **Phase 2 (High Impact, Medium Effort)**
4. **Stage 7: Dialectical for Synthesis** - +30-40% novelty
5. **Stage 5: Bayesian for Screening** - +25-35% accuracy
6. **Stage 20: Bayesian + Pre-Mortem for Quality Gate** - +25-35% QA

### **Phase 3 (Medium Impact, Nice to Have)**
7. **Stage 2: Socratic for Decomposition** - +20-25% completeness
8. **Stage 3-6: Research Method for Literature** - +20-40% coverage
9. **Stage 13: Pre-Mortem + Socratic for Refinement** - -40-50% repair cycles

---

## 🔗 References

- **Reasoner IMPLEMENTATION.md** — Source document
- **Berb Pipeline** — `berb/pipeline/stage_impls/`
- **Reasoner Methods** — `reasoner/methods/`

---

**Berb — Research, Refined.** 🧪✨
