"""
Batch Processor Service - Handle multiple contract files simultaneously.
"""
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import time
from dataclasses import dataclass
from datetime import datetime

from services.document_processor import DocumentProcessor, DocumentProcessingError
from services.nlp_analyzer import NLPAnalyzer
from services.compliance_checker import ComplianceChecker
from services.recommendation_engine import RecommendationEngine
from services.slack_notifier import SlackNotifier
from models.processed_document import ProcessedDocument
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BatchResult:
    """Result from processing a single file in batch."""
    filename: str
    success: bool
    processed_document: Optional[ProcessedDocument] = None
    analysis_results: Optional[Dict[str, Any]] = None
    compliance_results: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class BatchSummary:
    """Summary of batch processing results."""
    total_files: int
    successful: int
    failed: int
    total_time: float
    avg_time_per_file: float
    results: List[BatchResult]
    started_at: datetime
    completed_at: datetime


class BatchProcessor:
    """Process multiple contract files in parallel."""
    
    def __init__(
        self,
        max_workers: int = 4,
        max_files: int = 10,
        enable_slack: bool = True,
        slack_channel: Optional[str] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum number of parallel workers
            max_files: Maximum number of files to process in one batch
            enable_slack: Enable Slack notifications
            slack_channel: Slack channel for notifications
        """
        self.max_workers = max_workers
        self.max_files = max_files
        # Initialize services
        self.nlp_analyzer = NLPAnalyzer()
        # Only embed the framework selected for this batch; the general
        # checker defaults to warming every supported framework.
        self.compliance_checker = ComplianceChecker(precompute_embeddings=False)
        self.recommendation_engine = RecommendationEngine(use_llama=False)
        
        # Initialize Slack notifier
        self.slack_notifier = SlackNotifier(default_channel=slack_channel or "#compliance-alerts") if enable_slack else None
        
        logger.info(f"BatchProcessor initialized (max_workers={max_workers}, max_files={max_files}, slack={enable_slack})")
    
    def _process_file_with_name(
        self,
        file_path: str,
        original_filename: str,
        framework: str = "GDPR",
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> BatchResult:
        """
        Process a single file with a custom filename.
        
        Args:
            file_path: Path to the file
            original_filename: Original filename to use in result
            framework: Compliance framework
            progress_callback: Optional progress callback
            
        Returns:
            BatchResult with original filename
        """
        result = self.process_file(file_path, framework, progress_callback)
        result.filename = original_filename  # Override with original name
        return result
    
    def process_file(
        self,
        file_path: str,
        framework: str = "GDPR",
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> BatchResult:
        """
        Process a single contract file.
        
        Args:
            file_path: Path to the contract file
            framework: Compliance framework to check against
            progress_callback: Optional callback for progress updates
            
        Returns:
            BatchResult with processing outcome
        """
        filename = Path(file_path).name
        start_time = time.time()
        
        try:
            logger.info(f"Processing file: {filename}")
            
            # Skip progress callback if None (to avoid thread context issues)
            # Progress callbacks don't work from worker threads in Streamlit
            
            # Step 1: Extract and process document
            # Each worker owns its document/OCR processor; the analysis models
            # remain shared and can serve several files concurrently.
            processed_doc = DocumentProcessor().process_document(file_path)
            
            # Step 2: NLP analysis - analyze the clauses
            clause_analyses = self.nlp_analyzer.analyze_clauses(processed_doc.clauses)
            
            # Step 3: Compliance checking
            compliance_report = self.compliance_checker.check_compliance(
                clause_analyses,
                [framework],  # Pass as list
                processed_doc.document_id
            )
            
            # Step 4: Generate recommendations
            recommendations = self.recommendation_engine.generate_recommendations(
                compliance_report
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed {filename} in {processing_time:.2f}s")
            
            return BatchResult(
                filename=filename,
                success=True,
                processed_document=processed_doc,
                analysis_results=clause_analyses,
                compliance_results=compliance_report,
                recommendations=recommendations,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing {filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return BatchResult(
                filename=filename,
                success=False,
                error=error_msg,
                processing_time=processing_time
            )
    
    def process_batch(
        self,
        file_paths: List[str],
        framework: str = "GDPR",
        progress_callback: Optional[Callable[[str, float], None]] = None,
        original_filenames: Optional[List[str]] = None
    ) -> BatchSummary:
        """
        Process multiple contract files in parallel.
        
        Args:
            file_paths: List of file paths to process
            framework: Compliance framework to check against
            progress_callback: Optional callback for progress updates
            original_filenames: Optional list of original filenames (for temp files)
            
        Returns:
            BatchSummary with all results
        """
        if len(file_paths) > self.max_files:
            raise ValueError(f"Cannot process more than {self.max_files} files at once")
        
        # If original filenames not provided, extract from paths
        if original_filenames is None:
            original_filenames = [Path(p).name for p in file_paths]

        # Warm just the requirements used by this batch once, before workers
        # begin reading from the shared knowledge base.
        self.compliance_checker.knowledge_base.precompute_embeddings([framework])
        
        started_at = datetime.now()
        logger.info(f"Starting batch processing of {len(file_paths)} files")
        
        results = []
        
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks with original filenames
            future_to_file = {}
            for i, file_path in enumerate(file_paths):
                future = executor.submit(
                    self._process_file_with_name,
                    file_path,
                    original_filenames[i],
                    framework,
                    progress_callback
                )
                future_to_file[future] = (file_path, original_filenames[i])
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path, original_name = future_to_file[future]
                    logger.error(f"Exception processing {original_name}: {e}")
                    results.append(BatchResult(
                        filename=original_name,
                        success=False,
                        error=str(e)
                    ))
        
        completed_at = datetime.now()
        total_time = (completed_at - started_at).total_seconds()
        
        # Calculate summary statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        avg_time = total_time / len(results) if results else 0
        
        summary = BatchSummary(
            total_files=len(file_paths),
            successful=successful,
            failed=failed,
            total_time=total_time,
            avg_time_per_file=avg_time,
            results=results,
            started_at=started_at,
            completed_at=completed_at
        )
        
        logger.info(
            f"Batch processing complete: {successful}/{len(file_paths)} successful "
            f"in {total_time:.2f}s (avg {avg_time:.2f}s/file)"
        )
        
        # Send Slack notification if enabled
        if self.slack_notifier and self.slack_notifier.enabled:
            agg_metrics = self.get_aggregated_compliance_score(summary)
            self.slack_notifier.notify_batch_complete(
                total_files=summary.total_files,
                successful=summary.successful,
                failed=summary.failed,
                total_time=summary.total_time,
                avg_compliance_score=agg_metrics['average_score'],
                high_risk_count=agg_metrics['high_risk_count']
            )
        
        return summary
    
    @staticmethod
    def get_aggregated_compliance_score(summary: BatchSummary) -> Dict[str, Any]:
        """
        Calculate aggregated compliance metrics across all files.
        
        Args:
            summary: BatchSummary from process_batch()
            
        Returns:
            Dictionary with aggregated metrics
        """
        successful_results = [r for r in summary.results if r.success and r.compliance_results]
        
        if not successful_results:
            return {
                'overall_score': 0.0,
                'average_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'total_issues': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0
            }
        
        scores = []
        total_issues = 0
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for result in successful_results:
            # compliance_results is now a ComplianceReport object
            report = result.compliance_results
            scores.append(report.overall_score)
            total_issues += len(report.missing_requirements)
            
            # Count issues by risk level from summary
            risk_counts['high'] += report.summary.high_risk_count
            risk_counts['medium'] += report.summary.medium_risk_count
            risk_counts['low'] += report.summary.low_risk_count
        
        return {
            'overall_score': sum(scores) / len(scores) if scores else 0.0,
            'average_score': sum(scores) / len(scores) if scores else 0.0,
            'min_score': min(scores) if scores else 0.0,
            'max_score': max(scores) if scores else 0.0,
            'total_issues': total_issues,
            'high_risk_count': risk_counts['high'],
            'medium_risk_count': risk_counts['medium'],
            'low_risk_count': risk_counts['low'],
            'files_analyzed': len(successful_results)
        }
    
    def export_batch_results(
        self,
        summary: BatchSummary,
        output_format: str = 'json'
    ) -> str:
        """
        Export batch results to file.
        
        Args:
            summary: BatchSummary to export
            output_format: 'json' or 'csv'
            
        Returns:
            Path to exported file
        """
        from services.export_service import ExportService
        
        export_service = ExportService()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare data for export
        export_data = {
            'summary': {
                'total_files': summary.total_files,
                'successful': summary.successful,
                'failed': summary.failed,
                'total_time': summary.total_time,
                'avg_time_per_file': summary.avg_time_per_file,
                'started_at': summary.started_at.isoformat(),
                'completed_at': summary.completed_at.isoformat()
            },
            'aggregated_metrics': self.get_aggregated_compliance_score(summary),
            'results': []
        }
        
        # Add individual file results
        for result in summary.results:
            file_data = {
                'filename': result.filename,
                'success': result.success,
                'processing_time': result.processing_time,
                'error': result.error
            }
            
            if result.success and result.compliance_results:
                file_data.update({
                    'compliance_score': getattr(result.compliance_results, 'overall_score', 0),
                    'missing_clauses_count': len(getattr(result.compliance_results, 'missing_requirements', [])),
                    'high_risk_issues': getattr(getattr(result.compliance_results, 'summary', None), 'high_risk_count', 0)
                })
            
            export_data['results'].append(file_data)
        
        # Export using ExportService
        if output_format == 'json':
            output_path = f"reports/batch_results_{timestamp}.json"
            export_service._write_json(export_data, output_path)
        else:
            import pandas as pd
            df = pd.DataFrame(export_data['results'])
            output_path = f"reports/batch_results_{timestamp}.csv"
            df.to_csv(output_path, index=False)
        
        logger.info(f"Batch results exported to: {output_path}")
        return output_path
