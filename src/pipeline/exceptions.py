"""
Pipeline-specific exceptions for Issue #63

Custom exception classes for the unified data ingestion pipeline.
"""


class PipelineException(Exception):
    """Base exception for pipeline operations"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PipelineConfigurationError(PipelineException):
    """Raised when pipeline configuration is invalid"""
    pass


class SDMXParsingError(PipelineException):
    """Raised when SDMX XML parsing fails"""
    pass


class QualityValidationError(PipelineException):
    """Raised when data quality validation fails"""
    pass


class PipelineTimeoutError(PipelineException):
    """Raised when pipeline operation times out"""
    pass


class DataIngestionError(PipelineException):
    """Raised when data ingestion fails"""
    pass


class QualityThresholdError(PipelineException):
    """Raised when data quality falls below acceptable threshold"""
    
    def __init__(self, message: str, quality_score: float, threshold: float, details: dict = None):
        super().__init__(message, details)
        self.quality_score = quality_score
        self.threshold = threshold


class PipelineJobNotFoundError(PipelineException):
    """Raised when requested pipeline job is not found"""
    pass


class BatchProcessingError(PipelineException):
    """Raised when batch processing encounters errors"""
    
    def __init__(self, message: str, failed_datasets: list = None, details: dict = None):
        super().__init__(message, details)
        self.failed_datasets = failed_datasets or []