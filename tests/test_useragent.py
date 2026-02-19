"""Tests for user-agent rotation pool."""

from webscrape.useragent import USER_AGENTS, UserAgentRotator


class TestUserAgentRotator:
    def test_pool_not_empty(self):
        assert len(USER_AGENTS) >= 10

    def test_round_robin_rotation(self):
        rotator = UserAgentRotator()
        first = rotator.get_ua()
        second = rotator.get_ua()
        assert first != second

    def test_round_robin_wraps(self):
        agents = ["UA1", "UA2", "UA3"]
        rotator = UserAgentRotator(agents)
        results = [rotator.get_ua() for _ in range(6)]
        assert results == ["UA1", "UA2", "UA3", "UA1", "UA2", "UA3"]

    def test_random_ua_from_pool(self):
        rotator = UserAgentRotator()
        ua = rotator.get_random_ua()
        assert ua in USER_AGENTS

    def test_pool_size(self):
        rotator = UserAgentRotator()
        assert rotator.pool_size == len(USER_AGENTS)

    def test_custom_agents(self):
        custom = ["CustomBot/1.0", "CustomBot/2.0"]
        rotator = UserAgentRotator(custom)
        assert rotator.pool_size == 2
        assert rotator.get_ua() == "CustomBot/1.0"
        assert rotator.get_ua() == "CustomBot/2.0"
