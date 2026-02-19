import pytest


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
  <div class="items">
    <article class="item">
      <h2 class="title">First Item</h2>
      <p class="summary">Summary of first item</p>
      <a class="link" href="/item/1">Read more</a>
      <time class="date" datetime="2025-01-15">Jan 15, 2025</time>
    </article>
    <article class="item">
      <h2 class="title">Second Item</h2>
      <p class="summary">Summary of second item</p>
      <a class="link" href="/item/2">Read more</a>
      <time class="date" datetime="2025-02-20">Feb 20, 2025</time>
    </article>
    <article class="item">
      <h2 class="title">Third Item</h2>
      <p class="summary">Summary of third item</p>
      <a class="link" href="/item/3">Read more</a>
      <time class="date" datetime="2025-03-10">Mar 10, 2025</time>
    </article>
  </div>
  <a class="next-page" href="/page/2">Next</a>
</body>
</html>"""

SAMPLE_HTML_PAGE2 = """<!DOCTYPE html>
<html>
<head><title>Test Page 2</title></head>
<body>
  <div class="items">
    <article class="item">
      <h2 class="title">Fourth Item</h2>
      <p class="summary">Summary of fourth item</p>
      <a class="link" href="/item/4">Read more</a>
      <time class="date" datetime="2025-04-05">Apr 5, 2025</time>
    </article>
  </div>
</body>
</html>"""


@pytest.fixture
def sample_html():
    return SAMPLE_HTML


@pytest.fixture
def sample_html_page2():
    return SAMPLE_HTML_PAGE2


@pytest.fixture
def sample_config_dict():
    return {
        "name": "test-scrape",
        "base_url": "https://example.com",
        "urls": ["https://example.com/page/1"],
        "selectors": {
            "parser": "css",
            "items": "article.item",
            "fields": {
                "title": "h2.title::text",
                "summary": "p.summary::text",
                "url": "a.link::attr(href)",
                "date": "time.date::attr(datetime)",
            },
        },
        "export": {
            "format": "json",
            "output": "./output/test.json",
        },
    }


@pytest.fixture
def sample_config_yaml(tmp_path, sample_config_dict):
    import yaml

    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(yaml.dump(sample_config_dict))
    return config_file
