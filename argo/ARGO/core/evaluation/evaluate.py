"""
ARGO - Automatic Evaluation System
Tests RAG + LLM pipeline with predefined test cases
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bootstrap import initialize_argo
from core.config import get_config
from core.logger import get_logger

logger = get_logger("Evaluation")


class ARGOEvaluator:
    """
    Automated evaluation system for ARGO
    
    Tests:
    - RAG retrieval quality
    - LLM response accuracy
    - Project + Library integration
    - Response time
    """
    
    def __init__(self):
        self.config = get_config()
        self.eval_path = Path(__file__).parent
        self.results = []
    
    def load_test_cases(self) -> List[Dict]:
        """Load test cases from inputs/"""
        test_file = self.eval_path / "inputs" / "test_queries.json"
        
        if not test_file.exists():
            logger.warning(f"Test file not found: {test_file}")
            return self._create_default_test_cases()
        
        with open(test_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_default_test_cases(self) -> List[Dict]:
        """Create default test cases"""
        return [
            {
                "id": "test_001",
                "category": "general",
                "query": "What is the critical path in project management?",
                "expected_keywords": ["critical", "path", "longest", "sequence", "activities"],
                "should_use_library": True
            },
            {
                "id": "test_002",
                "category": "standards",
                "query": "According to PMI, what are the main process groups?",
                "expected_keywords": ["PMI", "initiating", "planning", "executing", "monitoring", "closing"],
                "should_use_library": True
            },
            {
                "id": "test_003",
                "category": "ed_sto",
                "query": "What are best practices for shutdown planning?",
                "expected_keywords": ["shutdown", "planning", "maintenance", "schedule", "resources"],
                "should_use_library": True
            }
        ]
    
    def run_evaluation(self, project_name: str = "EVAL_TEST") -> Dict[str, Any]:
        """
        Run complete evaluation
        
        Args:
            project_name: Test project name
        
        Returns:
            Dict with evaluation results
        """
        logger.info("Starting ARGO evaluation")
        
        # Initialize system
        try:
            argo = initialize_argo(project_name)
            model_router = argo['model_router']
            rag_engine = argo['project_components']['rag_engine']
            
            logger.info(f"System initialized for evaluation: {project_name}")
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
        
        # Load test cases
        test_cases = self.load_test_cases()
        logger.info(f"Loaded {len(test_cases)} test cases")
        
        # Run each test
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Running test {i}/{len(test_cases)}: {test_case['id']}")
            
            result = self._run_single_test(
                test_case,
                rag_engine,
                model_router,
                argo['project']['id']
            )
            
            results.append(result)
        
        # Generate summary
        summary = self._generate_summary(results)
        
        # Save results
        self._save_results(results, summary)
        
        return {
            "status": "completed",
            "summary": summary,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_single_test(
        self,
        test_case: Dict,
        rag_engine,
        model_router,
        project_id: str
    ) -> Dict:
        """Run single test case"""
        test_id = test_case['id']
        query = test_case['query']
        
        start_time = datetime.now()
        
        result = {
            "test_id": test_id,
            "category": test_case.get('category', 'general'),
            "query": query,
            "passed": False,
            "scores": {}
        }
        
        try:
            # 1. RAG Retrieval
            rag_start = datetime.now()
            
            search_results, metadata = rag_engine.search(
                query=query,
                top_k=5,
                include_library=test_case.get('should_use_library', True)
            )
            
            rag_time = (datetime.now() - rag_start).total_seconds()
            
            result["rag_time_ms"] = rag_time * 1000
            result["chunks_retrieved"] = len(search_results)
            result["library_used"] = metadata.get('library_used', False)
            result["library_chunks"] = metadata.get('library_results', 0)
            
            # 2. Generate response
            llm_start = datetime.now()
            
            context = rag_engine.format_context(search_results)
            
            messages = [
                {
                    "role": "system",
                    "content": f"You are a project management expert. Use the context below to answer.\n\n{context}"
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            response = model_router.run(
                task_type="chat",
                project_id=project_id,
                messages=messages
            )
            
            llm_time = (datetime.now() - llm_start).total_seconds()
            
            result["llm_time_ms"] = llm_time * 1000
            result["response"] = response.content
            result["tokens_used"] = response.usage.get('total_tokens', 0)
            
            # 3. Evaluate response quality
            scores = self._evaluate_response(
                response.content,
                test_case.get('expected_keywords', []),
                search_results
            )
            
            result["scores"] = scores
            result["passed"] = scores['overall'] >= 0.6
            
            # Total time
            total_time = (datetime.now() - start_time).total_seconds()
            result["total_time_ms"] = total_time * 1000
            
            result["status"] = "passed" if result["passed"] else "failed"
            
        except Exception as e:
            logger.error(f"Test {test_id} failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _evaluate_response(
        self,
        response: str,
        expected_keywords: List[str],
        search_results: List
    ) -> Dict[str, float]:
        """
        Evaluate response quality
        
        Returns:
            Dict with scores (0-1 range)
        """
        response_lower = response.lower()
        
        # 1. Keyword coverage
        if expected_keywords:
            keywords_found = sum(
                1 for kw in expected_keywords
                if kw.lower() in response_lower
            )
            keyword_score = keywords_found / len(expected_keywords)
        else:
            keyword_score = 1.0
        
        # 2. Response completeness (length-based heuristic)
        length_score = min(len(response) / 500, 1.0)  # Expect at least 500 chars
        
        # 3. RAG relevance (based on chunk scores)
        if search_results:
            avg_chunk_score = np.mean([r.score for r in search_results])
            relevance_score = avg_chunk_score
        else:
            relevance_score = 0.0
        
        # 4. Overall score (weighted average)
        overall = (
            keyword_score * 0.4 +
            length_score * 0.2 +
            relevance_score * 0.4
        )
        
        return {
            "keyword_coverage": round(keyword_score, 3),
            "completeness": round(length_score, 3),
            "rag_relevance": round(relevance_score, 3),
            "overall": round(overall, 3)
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate evaluation summary"""
        total = len(results)
        passed = sum(1 for r in results if r.get('passed', False))
        failed = sum(1 for r in results if r.get('status') == 'failed')
        errors = sum(1 for r in results if r.get('status') == 'error')
        
        # Average scores
        all_scores = [r['scores'] for r in results if 'scores' in r]
        
        if all_scores:
            avg_scores = {
                key: round(np.mean([s[key] for s in all_scores]), 3)
                for key in all_scores[0].keys()
            }
        else:
            avg_scores = {}
        
        # Average times
        rag_times = [r['rag_time_ms'] for r in results if 'rag_time_ms' in r]
        llm_times = [r['llm_time_ms'] for r in results if 'llm_time_ms' in r]
        total_times = [r['total_time_ms'] for r in results if 'total_time_ms' in r]
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "average_scores": avg_scores,
            "average_rag_time_ms": round(np.mean(rag_times), 1) if rag_times else 0,
            "average_llm_time_ms": round(np.mean(llm_times), 1) if llm_times else 0,
            "average_total_time_ms": round(np.mean(total_times), 1) if total_times else 0
        }
    
    def _save_results(self, results: List[Dict], summary: Dict):
        """Save evaluation results to file"""
        output_file = self.eval_path / "evaluation_results.json"
        
        output = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "summary": summary,
            "test_results": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Also create markdown report
        self._create_markdown_report(summary, results)
    
    def _create_markdown_report(self, summary: Dict, results: List[Dict]):
        """Create human-readable markdown report"""
        report_file = self.eval_path / "EVALUATION_REPORT.md"
        
        lines = [
            "# ARGO Evaluation Report",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Total Tests:** {summary['total_tests']}",
            f"- **Passed:** {summary['passed']} ({summary['pass_rate']}%)",
            f"- **Failed:** {summary['failed']}",
            f"- **Errors:** {summary['errors']}",
            "",
            "## Performance",
            "",
            f"- **Avg RAG Time:** {summary['average_rag_time_ms']:.1f} ms",
            f"- **Avg LLM Time:** {summary['average_llm_time_ms']:.1f} ms",
            f"- **Avg Total Time:** {summary['average_total_time_ms']:.1f} ms",
            "",
            "## Quality Scores",
            ""
        ]
        
        if summary.get('average_scores'):
            for key, value in summary['average_scores'].items():
                lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.3f}")
        
        lines.extend([
            "",
            "## Test Results",
            ""
        ])
        
        for result in results:
            status_emoji = "✅" if result.get('passed') else "❌"
            lines.extend([
                f"### {status_emoji} {result['test_id']} - {result['category']}",
                "",
                f"**Query:** {result['query']}",
                "",
                f"**Status:** {result.get('status', 'unknown')}",
                ""
            ])
            
            if 'scores' in result:
                lines.append("**Scores:**")
                for key, value in result['scores'].items():
                    lines.append(f"- {key}: {value:.3f}")
                lines.append("")
            
            if 'error' in result:
                lines.append(f"**Error:** {result['error']}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Markdown report saved to: {report_file}")


def main():
    """Main evaluation execution"""
    print("=" * 70)
    print("ARGO Automated Evaluation")
    print("=" * 70)
    
    evaluator = ARGOEvaluator()
    
    try:
        results = evaluator.run_evaluation()
        
        if results['status'] == 'completed':
            summary = results['summary']
            
            print(f"\n✓ Evaluation completed successfully")
            print(f"\nResults:")
            print(f"  Tests: {summary['total_tests']}")
            print(f"  Passed: {summary['passed']} ({summary['pass_rate']}%)")
            print(f"  Failed: {summary['failed']}")
            print(f"  Errors: {summary['errors']}")
            
            if summary.get('average_scores'):
                print(f"\nQuality Scores:")
                for key, value in summary['average_scores'].items():
                    print(f"  {key}: {value:.3f}")
            
            print(f"\nPerformance:")
            print(f"  Avg Total Time: {summary['average_total_time_ms']:.1f} ms")
            
            print(f"\nReports saved to evaluation/")
            
            # Exit code based on pass rate
            if summary['pass_rate'] >= 80:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print(f"\n✗ Evaluation failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Evaluation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
