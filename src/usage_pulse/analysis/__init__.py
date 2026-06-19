"""Analysis modules: ROI and model selection advisor."""

from .advisor import ModelAdvisor, Recommendation
from .roi import ModelROI, compute_roi

__all__ = ["ModelROI", "compute_roi", "ModelAdvisor", "Recommendation"]
