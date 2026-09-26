import spacy
from presidio_analyzer import AnalyzerEngine
from faker import Faker


def test_environment():
    nlp = spacy.load("en_core_web_lg")
    analyzer = AnalyzerEngine()
    fake = Faker()

    assert nlp is not None
    assert analyzer is not None
    assert fake is not None