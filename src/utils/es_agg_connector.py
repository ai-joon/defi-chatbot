import asyncio
import json
import aiohttp
import requests

from constants import KOAT_API_BASE, KOAT_API_KEY, TEST_TOKEN
from utils.add_message_to_queue import add_message_to_queue


class ESAggConnector:
    """A class that serves as the connection to Koat's News ES index"""

    endpoint = f"{KOAT_API_BASE}/p-sent*/_search/template"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {KOAT_API_KEY}",
    }

    async def get_text_async(self, query_string: str, **kwargs):
        results = await self.search_async(query_string, **kwargs)
        agg_filter = kwargs.get("agg_filter")
        message_queue = kwargs.get("message_queue", None)
        from_date = kwargs.get("from_date", "now-24h")
        to_date = kwargs.get("to_date", "now")

        if "error" in results:
            raise Exception("Failed to retrieve text")
        aggregations = results["aggregations"]
        text = ""
        interval = None
        match (agg_filter):
            case "sentiment":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents the change in sentiment from {from_date} to  {to_date} for both bots (manipulation) and organic social media activity (public) towards {query_string}. The sentiment is a score between -100 and 100.\n\n"
                labels = []
                data = []
                interval = aggregations["0"]["interval"]
                for bucket in buckets:
                    public = bucket["1"]["buckets"]["Public"]
                    manipulation = bucket["1"]["buckets"]["Manipulation"]
                    media = bucket["1"]["buckets"]["Media"]

                    man_value = manipulation["average"]["value"]
                    pub_value = public["average"]["value"]
                    media_value = media["average"]["value"]
                    if not man_value:
                        man_value = 0.5
                    if not pub_value:
                        pub_value = 0.5
                    if not media_value:
                        media_value = 0.5

                    text += f"{bucket['key_as_string'].split('T')[0]} {bucket['key_as_string'].split('T')[1][0:-10]}\n"
                    text += f"Document count: {bucket['doc_count']}\n"
                    text += f"Manipulation doc count: {manipulation['doc_count']}\n"
                    text += f"Manipulation value: {round(man_value  * 200 - 100,2)}\n"
                    text += f"Public doc count: {public['doc_count']}\n"
                    text += f"Public value: {round(pub_value * 200 - 100, 2)}\n"
                    text += f"Media doc count: {media['doc_count']}\n"
                    text += f"Media value: {round(media_value * 200 - 100, 2)}\n\n"

                    labels.append(bucket["key"])

                    data.append(
                        {
                            "Manipulation": man_value * 200 - 100,
                            "Public": pub_value * 200 - 100,
                            "Media": media_value * 200 - 100,
                        }
                    )

            case "engagement":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents the change in engagement from {from_date} to  {to_date} towards {query_string}. Engagement is represented by single numeric value.\n\n"
                labels = []
                data = []
                for bucket in buckets:
                    public = bucket["1"]["buckets"]["Public"]
                    manipulation = bucket["1"]["buckets"]["Manipulation"]
                    media = bucket["1"]["buckets"]["Media"]
                    text += f"{bucket['key_as_string'].split('T')[0]} {bucket['key_as_string'].split('T')[1][0:-10]}\n"
                    text += f"Public engagement score: {public['2']['value']}\n"
                    text += f"Public document count: {public['doc_count']}\n"
                    text += (
                        f"Manipulation engagement score: {manipulation['2']['value']}\n"
                    )
                    text += (
                        f"Manipulation document count: {manipulation['doc_count']}\n"
                    )
                    text += f"Media engagement score: {media['2']['value']}\n"
                    text += f"Media document count: {media['doc_count']}\n\n"

                    labels.append(bucket["key"])
                    data.append(
                        {
                            "Public": public["2"]["value"],
                            "Manipulation": manipulation["2"]["value"],
                            "Media": media["2"]["value"],
                        }
                    )

            case "impressions":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents the change in impressions from {from_date} to  {to_date} towards {query_string}. Engagement is represented by single numeric value.\n\n"
                labels = []
                data = []
                for bucket in buckets:
                    public = bucket["1"]["buckets"]["Public"]
                    manipulation = bucket["1"]["buckets"]["Manipulation"]
                    media = bucket["1"]["buckets"]["Media"]

                    text += f"{bucket['key_as_string'].split('T')[0]} {bucket['key_as_string'].split('T')[1][0:-10]}\n"

                    text += f"Public value: {public['2']['value']}\n"
                    text += f"Public document count: {public['doc_count']}\n"
                    text += f"Manipulation value: {manipulation['2']['value']}\n"
                    text += (
                        f"Manipulation document count: {manipulation['doc_count']}\n"
                    )
                    text += f"Media value: {media['2']['value']}\n"
                    text += f"Media document count: {media['doc_count']}\n\n"

                    labels.append(bucket["key"])
                    data.append(
                        {
                            "Manipulation": manipulation["2"]["value"],
                            "Public": public["2"]["value"],
                            "Media": media["2"]["value"],
                        },
                    )

            case "emotion":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents emotion from {from_date} to  {to_date} towards {query_string}. Each emotion is assigned a score.\n\n"
                labels = []
                data = []
                for bucket in buckets:
                    text += f"Emotion: {bucket['key']}\n"
                    text += f"Document count: {bucket['doc_count']}\n"
                    text += f"Score: {round(bucket['1']['value'], 2)}\n\n"
                    labels.append(bucket["key"])
                    data.append(
                        {
                            "emotion": bucket["key"],
                            "value": round(bucket["1"]["value"], 2),
                        }
                    )

            case "influence":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents the top authors from {from_date} to  {to_date} towards {query_string}.\n\n"
                labels = []
                data = []
                for bucket in buckets:
                    text += f"Author: {bucket['key']}\n"
                    text += f"Document count: {bucket['doc_count']}\n"
                    text += f"Score: {round(bucket['1']['value'], 2)}\n\n"
                    labels.append(bucket["key"])
                    data.append(round(bucket["1"]["value"], 2))

            case "manipulation":
                buckets = aggregations["0"]["buckets"]
                text += f"The following data represents the bot manipulated activity versus public organic activity from {from_date} to  {to_date} towards {query_string}.\n\n"
                text += f"Manipulation:\n"
                text += f"Manipulation document count: {buckets['Manipulation']['doc_count']}\n"
                text += (
                    f"Manipulation value: {buckets['Manipulation']['1']['value']}\n\n"
                )
                text += f"Public:\n"
                text += f"Public document count: {buckets['Public']['doc_count']}\n"
                text += f"Public value: {buckets['Public']['1']['value']}\n"

                labels = ["Manipulation", "Public"]
                data = [
                    buckets["Manipulation"]["1"]["value"],
                    buckets["Public"]["1"]["value"],
                ]
        if interval and interval == "1h":
            timescale = "hour"
        else:
            timescale = "day"

        output_data = {
            "labels": labels,
            "data": data,
            "timescale": timescale,
            "interval": interval if interval else None,
        }

        if message_queue:
            await add_message_to_queue(
                json.dumps(
                    {
                        "message_type": "tool_output",
                        "message": {
                            "tool": "agg",
                            "agg_filter": agg_filter,
                            "result": output_data,
                        },
                    }
                ),
                message_queue,
            )

        return text

    def search(self, query_string: str, **kwargs):
        body = json.dumps(self.body_builder(query_string, **kwargs))
        res = requests.get(
            self.endpoint,
            params={"source": body, "source_content_type": "application/json"},
            headers=self.headers,
        )
        res_json = res.json()
        return res_json

    async def search_async(self, query_string: str, **kwargs):
        body = json.dumps(self.body_builder(query_string, **kwargs))
        params = {"source": body, "source_content_type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.endpoint, params=params, headers=self.headers
            ) as response:
                res_json = await response.json()
                return res_json

    def body_builder(self, query_string: str, **kwargs):
        agg_filter = kwargs.get("agg_filter", None)
        from_date = kwargs.get("from_date", "now-24h")
        to_date = kwargs.get("to_date", "now")
        timezone = kwargs.get("timezone", "America/Edmonton")

        body = {
            "id": f"{agg_filter}",
            "params": {
                "query_string": query_string,
                "queried_gte": from_date,
                "queried_lte": to_date,
                "timezone": timezone,
            },
        }

        return body


if __name__ == "__main__":

    async def main():
        adapter = ESAggConnector()
        results = await adapter.get_text_async(
            "bitcoin",
            agg_filter="sentiment",
            from_date="now-7d",
            to_date="now",
            timezone="America/Edmonton",
        )

    asyncio.run(main())
