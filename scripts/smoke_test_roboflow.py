"""Roboflow smoke test. STRETCH. Feed a real frame from the demo video.

    ROBOFLOW_API_KEY=... python scripts/smoke_test_roboflow.py frame.jpg

Prints every prediction with class and confidence. If the classes are wrong
or empty on intraoral footage (expected: the model is panoramic-X-ray trained),
leave detect_teeth on the Terra vision path.
"""
