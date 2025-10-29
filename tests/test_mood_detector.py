from src.conversation.mood_detector import MoodDetector


def test_positive_mood_detection():
    detector = MoodDetector()
    analysis = detector.analyse("I feel great and excited today!")
    assert analysis.mood == "positive"
    assert analysis.confidence > 0.5


def test_neutral_when_no_keywords():
    detector = MoodDetector()
    analysis = detector.analyse("Just talking about weather.")
    assert analysis.mood == "neutral"
    assert analysis.confidence == 0.2
