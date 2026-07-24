"""Tests for task routing."""

from omniagent.router import classify, TaskType


def test_code_review():
    assert classify("review this code for security issues") == TaskType.CODE_REVIEW
    assert classify("audit this function for vulnerabilities") == TaskType.CODE_REVIEW
    assert classify("what's wrong with this python script") == TaskType.CODE_REVIEW


def test_code_generation():
    assert classify("write a React component") == TaskType.CODE_GENERATION
    assert classify("create a REST API endpoint") == TaskType.CODE_GENERATION
    assert classify("build a dockerfile") == TaskType.CODE_GENERATION


def test_translation():
    assert classify("translate this to Spanish") == TaskType.TRANSLATION
    assert classify("traducir esto al portugues") == TaskType.TRANSLATION
    assert classify("translate to French") == TaskType.TRANSLATION


def test_math():
    assert classify("solve this equation") == TaskType.MATH
    assert classify("calculate the derivative") == TaskType.MATH
    assert classify("what is the big O of this algorithm") == TaskType.MATH


def test_quick_query():
    assert classify("what is React") == TaskType.QUICK_QUERY
    assert classify("how do I install docker") == TaskType.QUICK_QUERY
    assert classify("tldr this article") == TaskType.QUICK_QUERY


def test_creative():
    assert classify("write a story about a robot") == TaskType.CREATIVE_WRITING
    assert classify("brainstorm marketing slogans") == TaskType.CREATIVE_WRITING


def test_general():
    assert classify("hello") == TaskType.GENERAL
    assert classify("random text with no signals") == TaskType.GENERAL
