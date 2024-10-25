from elasticsearch_dsl import analyzer, tokenizer

html_strip = analyzer(
    "html_strip",
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

autocomplete_analyzer = analyzer("autocomplete_analyzer",
    # tokenizer=tokenizer("trigram", "nGram", min_gram=2, max_gram=20),
    tokenizer=tokenizer("trigram", "edge_ngram", min_gram=2, max_gram=20),
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"]
)

