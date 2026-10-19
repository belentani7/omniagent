"""Tests for task routing."""

from omniagent.router import TaskType, classify


def test_code_review():
    assert classify("review this code for security issues") == TaskType.CODE_REVIEW
    assert classify("audit this function for vulnerabilities") == TaskType.CODE_REVIEW
    assert classify("what's wrong with this script") == TaskType.CODE_REVIEW


def test_code_generation():
    assert classify("write a component") == TaskType.CODE_GENERATION
    assert classify("create a REST endpoint") == TaskType.CODE_GENERATION
    assert classify("build a container") == TaskType.CODE_GENERATION


def test_translation():
    assert classify("translate this to Spanish") == TaskType.TRANSLATION
    assert classify("translate to Portuguese") == TaskType.TRANSLATION
    assert classify("translate to French") == TaskType.TRANSLATION


def test_math():
    assert classify("solve this equation") == TaskType.MATH
    assert classify("calculate the derivative") == TaskType.MATH
    assert classify("what is the complexity of this") == TaskType.MATH


def test_quick_query():
    assert classify("what is a REST API") == TaskType.QUICK_QUERY
    assert classify("how do I install something") == TaskType.QUICK_QUERY
    assert classify("tldr this article") == TaskType.QUICK_QUERY


def test_creative():
    assert classify("write a story about a robot") == TaskType.CREATIVE_WRITING
    assert classify("brainstorm marketing slogans") == TaskType.CREATIVE_WRITING


def test_general():
    assert classify("hello") == TaskType.GENERAL
    assert classify("random text with no signals") == TaskType.GENERAL


def test_spanish_and_catalan_signals_are_normalized():
    assert classify("Revisa este código por seguridad") == TaskType.CODE_REVIEW
    assert classify("Calcular la derivada de x") == TaskType.MATH
    assert classify("Vull traduir aquest text al català") == TaskType.TRANSLATION
    assert classify("Compara els millors models") == TaskType.RESEARCH


def test_signal_matching_uses_word_boundaries():
    assert classify("A builder is rebuilding something") == TaskType.GENERAL


def test_classify_rejects_non_string_prompts():
    import pytest

    with pytest.raises(TypeError, match="prompt must be a string"):
        classify(None)
