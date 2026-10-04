"""TrafficVision - AI traffic sign detection system."""

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass

__version__ = "0.1.0"
