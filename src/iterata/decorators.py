"""
Decorators for automatic correction tracking
"""

from functools import wraps
from typing import Callable, Optional, Any


def with_correction_tracking(
    base_path: str,
    auto_explain: bool = False,
    skill_path: Optional[str] = None,
    explainer: Optional[Any] = None,
):
    """
    Decorator pour tracker automatiquement les corrections.

    This decorator attaches a CorrectionLoop instance to the decorated function,
    allowing easy logging of corrections during execution.

    Args:
        base_path: Base directory for storing corrections
        auto_explain: Enable automatic explanation (requires explainer)
        skill_path: Path where to generate skills (optional)
        explainer: Explainer instance for auto-explanation (optional)

    Returns:
        Decorated function with correction tracking capabilities

    Usage:
        @with_correction_tracking(base_path="./corrections")
        def extract_invoice(image_path: str) -> dict:
            result = my_extraction_logic(image_path)
            return result

        # Then log corrections:
        extract_invoice.log_correction(
            original="1,234.56",
            corrected="1234.56",
            document_id="invoice_001.pdf",
            field_path="total_amount"
        )
    """
    from .loop import CorrectionLoop

    loop = CorrectionLoop(
        base_path=base_path, skill_path=skill_path, explainer=explainer, auto_explain=auto_explain
    )

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Attache le loop à l'objet result si possible
            if hasattr(result, "__dict__"):
                result._iterata_loop = loop

            return result

        # Attache la fonction de logging directement au wrapper
        def log_correction(original, corrected, document_id, **log_kwargs):
            """
            Log a correction for this function.

            Args:
                original: Original extracted value
                corrected: Corrected value
                document_id: Document identifier
                **log_kwargs: Additional arguments (field_path, context, etc.)

            Returns:
                Correction object
            """
            # Ajoute le nom de la fonction au contexte
            if "context" not in log_kwargs:
                log_kwargs["context"] = {}

            log_kwargs["context"]["function"] = func.__name__

            return loop.log(original=original, corrected=corrected, document_id=document_id, **log_kwargs)

        # Attache les méthodes utiles au wrapper
        wrapper.log_correction = log_correction
        wrapper.get_stats = loop.get_stats
        wrapper.get_summary = loop.get_summary
        wrapper.update_skill = loop.update_skill
        wrapper.check_readiness = loop.check_skill_readiness
        wrapper._iterata_loop = loop

        return wrapper

    return decorator


def track_corrections(loop_instance: "CorrectionLoop"):
    """
    Alternative decorator using an existing CorrectionLoop instance.

    Args:
        loop_instance: Existing CorrectionLoop to use

    Usage:
        from iterata import CorrectionLoop

        loop = CorrectionLoop(base_path="./corrections")

        @track_corrections(loop)
        def extract_data(document_path: str) -> dict:
            # Your extraction logic
            return extracted_data
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Attache le loop
            if hasattr(result, "__dict__"):
                result._iterata_loop = loop_instance

            return result

        # Attache les méthodes
        def log_correction(original, corrected, document_id, **log_kwargs):
            if "context" not in log_kwargs:
                log_kwargs["context"] = {}
            log_kwargs["context"]["function"] = func.__name__

            return loop_instance.log(
                original=original, corrected=corrected, document_id=document_id, **log_kwargs
            )

        wrapper.log_correction = log_correction
        wrapper.get_stats = loop_instance.get_stats
        wrapper.get_summary = loop_instance.get_summary
        wrapper.update_skill = loop_instance.update_skill
        wrapper._iterata_loop = loop_instance

        return wrapper

    return decorator
