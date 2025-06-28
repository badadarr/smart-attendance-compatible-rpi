# Quality Configuration for Face Recognition System
# This file allows easy adjustment of quality thresholds without modifying main code

# Quality Threshold Presets
# Adjust these values based on your camera quality and environmental conditions

QUALITY_PRESETS = {
    "very_strict": {
        "threshold": 0.85,
        "description": "Excellent quality only - best for high-end cameras in good lighting",
        "recommended_for": "High security environments, good cameras",
    },
    "strict": {
        "threshold": 0.75,
        "description": "Good quality required - previous default setting",
        "recommended_for": "Standard office environments with decent cameras",
    },
    "moderate": {
        "threshold": 0.65,
        "description": "Acceptable quality - balanced between accuracy and accessibility",
        "recommended_for": "Mixed lighting conditions, average cameras",
    },
    "relaxed": {
        "threshold": 0.55,
        "description": "Lower quality accepted - current default setting",
        "recommended_for": "Poor lighting, older cameras, Raspberry Pi cameras",
    },
    "very_relaxed": {
        "threshold": 0.45,
        "description": "Minimal quality check - use with caution",
        "recommended_for": "Very poor conditions, last resort option",
    },
}

# Current active preset (change this to adjust system behavior)
ACTIVE_PRESET = (
    "relaxed"  # Change this to: very_strict, strict, moderate, relaxed, or very_relaxed
)

# Or set a custom threshold (0.0 to 1.0)
# If CUSTOM_THRESHOLD is not None, it will override ACTIVE_PRESET
CUSTOM_THRESHOLD = None  # Example: 0.50 for custom 50% threshold

# Quality calculation weights (advanced settings)
# These control how different factors contribute to the overall quality score
QUALITY_WEIGHTS = {
    "area_score": 0.3,  # Face size relative to frame
    "sharpness_score": 0.4,  # Image focus/clarity
    "brightness_score": 0.2,  # Lighting conditions
    "symmetry_score": 0.1,  # Face symmetry
}

# Sharpness detection sensitivity
SHARPNESS_VARIANCE_THRESHOLD = 500.0  # Lower = more strict, Higher = more lenient

# Face area requirements
MIN_FACE_AREA_RATIO = 0.02  # Minimum face area relative to frame (2%)


def get_active_threshold():
    """Get the currently active quality threshold"""
    if CUSTOM_THRESHOLD is not None:
        return CUSTOM_THRESHOLD
    return QUALITY_PRESETS[ACTIVE_PRESET]["threshold"]


def get_active_description():
    """Get description of current setting"""
    if CUSTOM_THRESHOLD is not None:
        return f"Custom threshold: {CUSTOM_THRESHOLD}"
    return QUALITY_PRESETS[ACTIVE_PRESET]["description"]


def print_current_settings():
    """Print current quality settings"""
    print("🔧 Current Quality Settings:")
    print(f"   Threshold: {get_active_threshold()}")
    print(f"   Description: {get_active_description()}")
    print(f"   Weights: {QUALITY_WEIGHTS}")
