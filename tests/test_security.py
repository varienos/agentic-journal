from agent_journal.security import redact_value


def test_redacts_known_secret_keys():
    value = redact_value({"OPENAI_API_KEY": "sk-secret", "safe": "ok"})

    assert value["OPENAI_API_KEY"] == "[REDACTED]"
    assert value["safe"] == "ok"


def test_redacts_bearer_tokens_in_strings():
    value = redact_value("Authorization: Bearer abcdef123456")

    assert "abcdef123456" not in value
    assert "[REDACTED]" in value


def test_redacts_nested_values():
    value = redact_value({"semantic": {"note": "GEMINI_API_KEY=secret-value"}})

    assert "secret-value" not in value["semantic"]["note"]

