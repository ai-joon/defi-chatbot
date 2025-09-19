from typing import List, Literal

from utils.remove_unicode import remove_unicode


def extract_text_from_es_results(
    es_results: dict,
    min_tweet_length: int = 4,
) -> str:
    return_value = ""
    for result in es_results:
        doc = result["_source"]
        text = doc["text"]
        if "http" not in text and len(text.split(" ")) > min_tweet_length:
            combined_text = f"Author: {doc['author']}\n"
            combined_text += f"Source: {doc['publication']}\n"
            combined_text += f"Content: {remove_unicode(text)}\n\n"
            return_value += combined_text
    return return_value


def build_filters(**kwargs) -> List:

    score: dict = kwargs.get("score", {"gte": 1000})
    sentiment = kwargs.get("sentiment", None)
    emotion = kwargs.get("emotion", None)
    influence: Literal["bot", "susbot", "organic", "media", "socials"] = kwargs.get(
        "influence", None
    )
    proper_nouns: str = kwargs.get("proper_nouns", None)
    content_type: str = kwargs.get("content_type", None)
    from_date: str = kwargs.get("from_date", "now-24h")
    to_date: str = kwargs.get("to_date", "now")
    timezone: str = kwargs.get("timezone", "America/Edmonton")

    filters = [
        {
            "range": {
                "@timestamp": {
                    "format": "strict_date_optional_time",
                    "gte": from_date,
                    "lte": to_date,
                    "time_zone": timezone if timezone else "America/Edmonton",
                }
            }
        }
    ]

    if influence:
        filters.append(
            {
                "query_string": {
                    "query": influence,
                    "default_field": "bot.keyword",
                }
            }
        )

    if emotion:
        filters.append(
            {
                "query_string": {
                    "query": emotion,
                    "default_field": "body.emotion.type.keyword",
                }
            }
        )
    if sentiment:
        filters.append(
            {
                "query_string": {
                    "query": sentiment,
                    "default_field": "textSentiment.polarity.keyword",
                }
            }
        )
    if score:
        filters.append(
            {"range": {"score": score}},
        )
    if proper_nouns:
        filters.append(
            {
                "query_string": {
                    "query": proper_nouns,
                    "default_field": "text",
                }
            }
        )

    if content_type:
        filters.append({"term": {"type.keyword": content_type}})

    return filters
