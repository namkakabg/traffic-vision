"""Inference protocols and adapters for TrafficVision."""

from trafficvision.inference.base import PredictionContractError, Predictor
from trafficvision.inference.ultralytics import UltralyticsOnnxPredictor

__all__ = ["PredictionContractError", "Predictor", "UltralyticsOnnxPredictor"]
