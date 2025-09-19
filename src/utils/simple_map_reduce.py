import asyncio
import logging
from llms import llms

logger = logging.getLogger("app")


def split_text(text, num_splits):
    part_length = len(text) // num_splits
    split_points = [part_length * (i + 1) for i in range(num_splits - 1)]
    for i in range(num_splits - 1):
        while split_points[i] < len(text) and text[split_points[i]] != " ":
            split_points[i] += 1
    parts = []
    previous_point = 0
    for point in split_points:
        parts.append(text[previous_point:point].strip())
        previous_point = point
    parts.append(text[previous_point:].strip())
    return parts


async def simple_map_reduce(
    text: str, mr_prompt, combine_prompt, mr_llm="gpt4o", combine_llm="gpt4o"
):
    mr_llm = llms[mr_llm]
    combine_llm = llms[combine_llm]

    mr_formatted_prompt = mr_prompt.format(text=text)

    prompt_token_count = len(mr_llm["tokenizer"].encode(mr_formatted_prompt))
    logger.debug(f"Prompt token count: {prompt_token_count}")

    # plus 1000 for response tokens
    if prompt_token_count + 1000 > mr_llm["token_limit"]:
        num_chunks = ((prompt_token_count + 1000) // mr_llm["token_limit"]) + 1
        logger.debug(f"Prompt token count: {num_chunks}")
        chunks = split_text(text, num_chunks)
        tasks = []
        for chunk in chunks:
            tasks.append(mr_llm["llm"].ainvoke(mr_prompt.format(text=chunk)))
        combine_context = "\n\n".join(
            [result.content for result in await asyncio.gather(*tasks)]
        )

        return (
            await combine_llm["llm"].ainvoke(
                combine_prompt.format(text=combine_context)
            )
        ).content

    return (await mr_llm["llm"].ainvoke(mr_formatted_prompt)).content


if __name__ == "__main__":
    from prompts.summarize.news_mr import news_mr_prompt, news_combine_prompt
    from tag_extraction import extract_tags

    topic_prompt = "Test Topic"
    text = "Test Text"

    async def main():
        combine_prompt = news_combine_prompt.format(
            topic_prompt=topic_prompt, text="{text}"
        )
        mr_prompt = news_mr_prompt.format(topic_prompt=topic_prompt, text="{text}")

        response = await simple_map_reduce(text, mr_prompt, combine_prompt)
        print(extract_tags(response))

    asyncio.run(main())
