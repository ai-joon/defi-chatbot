news_mr_prompt = """
The content between the <context> tags contains news articles. The content between the <topic> tags is information that will help you perform your task.

<topic>The news article(s) are about {topic_prompt}</topic>

Given the above information, your task is to take the following news article(s), and write a concise summary of the topics without any bias. Do your best to group the content into categories. For each category, include the number of articles that fall into that category. Do your best NOT to summarize individual articles, if it fits into that category incorporate the article into that category's summary. If a article doesn't fit into any existing categories but its still relevant to the topic, its okay to summarize it on its own. These articles have been provided by simple search queries, 
so it is possible the articles contain irrelevant information to the provided topic. Please note the irrelevant topics separate from your summary between <irrelevant> tags. Please wrap your summary in <summary> tags. Keep the summary and irrelevant tags separate, do not nest them.

When adding the irrelevant section, give an extremely concise summary of the irrelevant content. Since it is irrelevant, we don't require much detail.

Include the article count in parentheses after the category name e.g. (10 articles).

<context>{text}</context>

Remember, do not nest your response tags, keep them separate.
i.e. Like this: <summary>YOUR SUMMARY</summary><irrelevant>IRRELEVANT INFO</irrelevant>
NOT LIKE THIS: <summary>YOUR SUMMARY<irrelevant>IRRELEVANT INFO</irrelevant></summary>

Lastly, you must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.

Formatting rules:
1. You must use markdown
2. The category subheaders should just be bolded
3. The category subheader should be followed by a single new line character, and the category content should be followed by two new line characters
4. Do not use lists, just separate using new line characters

SUMMARY:
"""

news_combine_prompt = """
The content between the <context> tags contains summaries of news articles (that have been summarized by a different llm). The content between the <topic> tags is information that will help you perform your task.

<topic>The news articles were about {topic_prompt}</topic>

Given the above information, your task is to take the following news articles summaries, and write a concise summary of the topics across the other summaries without any bias. Do your best to group the content into categories. For each category, include the number of articles that fall into that category. Do your best NOT to summarize individual articles, if it fits into that category incorporate the article into that category's summary. If a article doesn't fit into any existing categories but its still relevant to the topic, its okay to summarize it on its own. These articles have been provided by simple search queries, 
so it was possible the articles contained irrelevant information to the provided topic. Please note the irrelevant topics separate from your summary between <irrelevant> tags. Please wrap your summary in <summary> tags. Keep the summary and irrelevant tags separate, do not nest them.

When adding the irrelevant section, give an extremely concise summary of the irrelevant content. Since it is irrelevant, we don't require much detail.

Include the article count in parentheses after the category name e.g. (10 articles).

<context>{text}</context>

Remember, do not nest your response tags, keep them separate.
i.e. Like this: <summary>YOUR SUMMARY</summary><irrelevant>IRRELEVANT INFO</irrelevant>
NOT LIKE THIS: <summary>YOUR SUMMARY<irrelevant>IRRELEVANT INFO</irrelevant></summary>

Lastly, you must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.

Formatting rules:
1. You must use markdown
2. The category subheaders should just be bolded
3. The category subheader should be followed by a single new line character, and the category content should be followed by two new line characters
4. Do not use lists, just separate using new line characters

SUMMARY:
"""
