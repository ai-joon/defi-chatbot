import asyncio
import json
import logging
from typing import Literal
import aiohttp
from rich import print
from constants import KOAT_API_BASE, KOAT_API_KEY
from aiohttp import ClientTimeout

from utils.es_helpers import build_filters, extract_text_from_es_results


logger = logging.getLogger("app")


class ESConnector:
    """A class that serves as the connection to Koat's ES index"""

    psent_endpoint = f"{KOAT_API_BASE}/p-sent*/_search"
    sparse_endpoint = f"{KOAT_API_BASE}/_search/template"
    alert_endpoint = f"{KOAT_API_BASE}/p-sent-*/_search/template"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {KOAT_API_KEY}",
    }

    async def get_text_async(self, search_text: str, **kwargs):
        results = await self.search_async(search_text, **kwargs)
        min_tweet_length = kwargs.get("min_tweet_length", 4)
        text = extract_text_from_es_results(results, min_tweet_length=min_tweet_length)
        return text

    async def search_async(self, search_text: str, **kwargs):
        body = json.dumps(self.body_builder(search_text, **kwargs))
        params = {"source": body, "source_content_type": "application/json"}
        async with aiohttp.ClientSession(timeout=ClientTimeout(120)) as session:
            async with session.get(
                self.psent_endpoint, params=params, headers=self.headers
            ) as response:
                res_json = await response.json()
                if "error" in res_json:
                    logger.error(res_json["error"])
                    raise Exception("Error in ES request in search_async")
                return res_json["hits"]["hits"]

    async def sparse_query_async(self, search_text: str, **kwargs):
        sentiment = kwargs.get("sentiment", "*")
        emotion = kwargs.get("emotion", "*")
        influence = kwargs.get("influence", "*")
        from_date = kwargs.get("from_date", "now-24h")
        to_date = kwargs.get("to_date", "now")
        timezone = kwargs.get("timezone", "America/Edmonton")

        body = json.dumps(
            {
                "id": "sparse_results",
                "params": {
                    "query_string": search_text,
                    "sentiment_string": sentiment,
                    "emotion_string": emotion,
                    "influence_string": influence,
                    "queried_gte": from_date,
                    "queried_lte": to_date,
                    "timezone": timezone,
                },
            }
        )
        params = {"source": body, "source_content_type": "application/json"}
        async with aiohttp.ClientSession(timeout=ClientTimeout(120)) as session:
            async with session.get(
                self.sparse_endpoint, params=params, headers=self.headers
            ) as response:
                res_json = await response.json()
                return res_json["aggregations"]["sparse_results"]["buckets"]

    async def alert_query_async(
        self, alert_id: str, type: Literal["scheduled", "anomaly"], **kwargs
    ):
        from_date = kwargs.get("from_date", "now-24h")
        to_date = kwargs.get("to_date", "now")
        if type == "scheduled":
            body = json.dumps(
                {
                    "id": "alerts_search",
                    "params": {"alert_id": alert_id, "gte": from_date, "lte": to_date},
                }
            )
        if type == "anomaly":
            body = json.dumps(
                {
                    "id": "clients_search",
                    "params": {"client_id": alert_id, "gte": from_date, "lte": to_date},
                }
            )

        params = {"source": body, "source_content_type": "application/json"}
        async with aiohttp.ClientSession(timeout=ClientTimeout(120)) as session:
            async with session.get(
                self.alert_endpoint, params=params, headers=self.headers
            ) as response:
                res_json = await response.json()
                return res_json["hits"]["hits"]

    def body_builder(self, search_text: str, **kwargs):
        num_candidates = kwargs.get("num_candidates", 10000)
        size = kwargs.get("size", 1500)
        k = kwargs.get("k", size)
        min_score = kwargs.get("min_score", 0.5)
        query_type = kwargs.get("query_type", "similarity")

        body = {
            "size": size,
            "track_total_hits": True,
            "_source": [
                "text",
                "author",
                "timestamp",
                "publication",
                "textSentiment",
                "mentions",
                "likes",
                "score",
                "bot",
                "tags",
                "url",
            ],
        }

        if query_type == "similarity":
            body["min_score"] = min_score
            body["knn"] = {
                "field": "text_embedding.predicted_value",
                "query_vector_builder": {
                    "text_embedding": {
                        "model_id": "sentence-transformers__msmarco-minilm-l-12-v3",
                        "model_text": search_text,
                    }
                },
                "k": k,
                "num_candidates": num_candidates,
                "filter": build_filters(**kwargs),
            }
        elif query_type == "query":
            body["query"] = {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "query_string": {
                                "query": search_text,
                                "fields": ["text", "author.keyword"],
                            }
                        },
                        *build_filters(**kwargs),
                    ],
                    "should": [],
                    "must_not": [],
                }
            }
        elif query_type == "author":
            body["query"] = {
                "bool": {
                    "must": [],
                    "filter": [
                        {
                            "query_string": {
                                "query": search_text,
                                "fields": ["author.keyword"],
                            }
                        },
                        *build_filters(**kwargs),
                    ],
                    "should": [],
                    "must_not": [],
                }
            }
        logger.debug(f"Socials body:")
        logger.debug(body)
        return body


if __name__ == "__main__":

    async def main():
        adapter = ESConnector()
        print(
            (
                await adapter.get_text_async(
                    "rbc",
                    from_date="now-12d",
                    size="3",
                    influence="media",
                    emotion="anger",
                )
            )
        )

    asyncio.run(main())
