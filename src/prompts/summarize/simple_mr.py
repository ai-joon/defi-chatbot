simple_mr_prompt = """
The content between the <context> tags contains social media posts and news articles from various platforms and news outlets. The content between the <topic> tags is information that will help you perform your task.

Given the above information, your task is to take the following social media posts and news articles, and write a meaningful summary. Do your best to group the content into categories. Please wrap your summary in <summary> tags.

<context>{text}</context>

You must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.
CONCISE SUMMARY:
"""

simple_combine_prompt = """
The content between the <context> tags contains summaries of social media posts and news articles (that have been summarized by a different llm). The content between the <topic> tags is information that will help you perform your task.

Given the above information, your task is to take the following social media post summaries, and write a concise summary of the topics across the other summaries. Do your best to group the content into categories. Please wrap your summary in <summary> tags.

<context>{text}</context>

You must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.
CONCISE SUMMARY:
"""
