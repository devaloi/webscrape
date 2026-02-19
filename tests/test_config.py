"""Tests for YAML config loader."""

import pytest
import yaml

from webscrape.config import ConfigError, load_config, load_config_from_dict


class TestLoadConfig:
    def test_valid_config(self, sample_config_yaml):
        config = load_config(sample_config_yaml)
        assert config.name == "test-scrape"
        assert config.base_url == "https://example.com"
        assert len(config.urls) == 1
        assert config.selectors.parser == "css"
        assert config.export.format == "json"

    def test_missing_file(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            load_config(tmp_path / "nonexistent.yaml")

    def test_missing_name(self, tmp_path):
        cfg = tmp_path / "bad.yaml"
        cfg.write_text(yaml.dump({"base_url": "https://example.com"}))
        with pytest.raises(ConfigError, match="name"):
            load_config(cfg)

    def test_missing_base_url(self, tmp_path):
        cfg = tmp_path / "bad.yaml"
        cfg.write_text(yaml.dump({"name": "test"}))
        with pytest.raises(ConfigError, match="base_url"):
            load_config(cfg)

    def test_defaults_applied(self, tmp_path):
        cfg = tmp_path / "minimal.yaml"
        cfg.write_text(yaml.dump({"name": "test", "base_url": "https://example.com"}))
        config = load_config(cfg)
        assert config.pagination.enabled is False
        assert config.pagination.max_pages == 10
        assert config.rate_limit.requests_per_second == 2.0
        assert config.rate_limit.burst == 5
        assert config.retry.max_attempts == 3
        assert config.retry.backoff_base == 1.0
        assert config.export.format == "json"
        assert config.urls == []
        assert config.headers == {}

    def test_invalid_yaml(self, tmp_path):
        cfg = tmp_path / "bad.yaml"
        cfg.write_text("just a string")
        with pytest.raises(ConfigError, match="mapping"):
            load_config(cfg)


class TestLoadConfigFromDict:
    def test_valid_dict(self, sample_config_dict):
        config = load_config_from_dict(sample_config_dict)
        assert config.name == "test-scrape"
        assert config.selectors.fields["title"] == "h2.title::text"

    def test_missing_name(self):
        with pytest.raises(ConfigError, match="name"):
            load_config_from_dict({"base_url": "https://example.com"})

    def test_missing_base_url(self):
        with pytest.raises(ConfigError, match="base_url"):
            load_config_from_dict({"name": "test"})
