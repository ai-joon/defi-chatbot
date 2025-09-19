socials_mr_prompt = """
The content between the <context> tags contains social media posts from various platforms. The content between the <topic> tags is information that will help you perform your task.

<topic>The social media posts are about {topic_prompt}</topic>

Given the above information, your task is to take the following social media posts, and write a meaningful summary of what social media users are talking about surrounding the topic. When highlighting a topic, also include which users on which platforms are talking about it. Do your best to group the conversations into categories. For each category, include the number of posts that fall into that category. Do your best NOT to summarize individual posts, if it fits into that category incorporate the post into that category's summary. If a post doesn't fit into any existing categories but its still relevant to the topic, its okay to summarize it on its own. These social media posts have been provided by simple social listening search queries, 
so it is possible the social media posts contain irrelevant information to the provided topic. Please note the irrelevant topics separate from your summary between <irrelevant> tags. Please wrap your summary in <summary> tags. Keep the summary and irrelevant tags separate, do not nest them.

When adding the irrelevant section, give an extremely concise summary of the irrelevant content. Since it is irrelevant, we don't require much detail.

Include the post count in parentheses after the category name e.g. (10 posts).

<context>{text}</context>

Remember, do not nest your response tags, keep them separate.
i.e. Like this: <summary>YOUR SUMMARY</summary><irrelevant>IRRELEVANT INFO</irrelevant>
NOT LIKE THIS: <summary>YOUR SUMMARY<irrelevant>IRRELEVANT INFO</irrelevant></summary>

In the context, posts from bot accounts will be labelled with "Account type: Bot Account", and organic users will be labelled with "Account type: Organic User". 
Please separate what narratives are being discussed by bot accounts versus organic users. Label bot conversations as "Manipulation" and organic conversations as "Organic Conversation".  If there are no posts labeled with "Bot Account", you can exclude the Manipulation section.

Lastly, you must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.


Formatting rules:
1. You must use markdown
2. The 'Manipulation' and 'Organic Conversation' subheaders should use '###'
3. The category subheaders should just be bolded
4. The category subheader should be followed by a single new line character, and the category content should be followed by two new line characters
5. Do not use lists, just separate using new line characters

SUMMARY:
"""

socials_combine_prompt = """
The content between the <context> tags contains summaries of social media posts (that have been summarized by a different llm). The content between the <topic> tags is information that will help you perform your task.

<topic>The social media posts were about {topic_prompt}</topic>

Given the above information, your task is to take the following social media post summaries, and write a concise summary of the topics across the other summaries without any bias. Do your best to group the conversations into categories. For each category, include the number of posts that fall into that category. Do your best NOT to summarize individual posts, if it fits into that category incorporate the post into that category's summary. If a post doesn't fit into any existing categories but its still relevant to the topic, its okay to summarize it on its own. These articles have been provided by simple search queries, 
so it was possible the articles contained irrelevant information to the provided topic. Please note the irrelevant topics separate from your summary between <irrelevant> tags. Please wrap your summary in <summary> tags. Keep the summary and irrelevant tags separate, do not nest them.

When adding the irrelevant section, give an extremely concise summary of the irrelevant content. Since it is irrelevant, we don't require much detail.

Include the post count in parentheses after the category name e.g. (10 posts). 

<context>{text}</context>

Remember, do not nest your response tags, keep them separate.
i.e. Like this: <summary>YOUR SUMMARY</summary><irrelevant>IRRELEVANT INFO</irrelevant>
NOT LIKE THIS: <summary>YOUR SUMMARY<irrelevant>IRRELEVANT INFO</irrelevant></summary>

In the context, posts from bot accounts will be labelled with "Account type: Bot Account", and organic users will be labelled with "Account type: Organic User". 
Please separate what narratives are being discussed by bot accounts versus organic users. Label bot conversations as "Manipulation" and organic conversations as "Organic Conversation". If there are no posts labeled with "Bot Account", you can exclude the Manipulation section.

Lastly, you must ONLY rely on the the information between the context tags. If there is nothing relevant to the topic, just say there is nothing relevant in the context.

Formatting rules:
1. You must use markdown
2. The 'Manipulation' and 'Organic Conversation' subheaders should use '###'
3. The category subheaders should just be bolded
4. The category subheader should be followed by a single new line character, and the category content should be followed by two new line characters
5. Do not use lists, just separate using new line characters

SUMMARY:
"""
