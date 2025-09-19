from langchain.prompts.loading import load_prompt

prompt_crafter_prompt = load_prompt("src/prompts/prompt-crafter.yaml")
authors_combine_prompt = load_prompt("src/prompts/authors-combine.yaml")
authors_mr_prompt = load_prompt("src/prompts/authors-map-reduce.yaml")
socials_mr_prompt = load_prompt("src/prompts/socials-map-reduce.yaml")
news_mr_prompt = load_prompt("src/prompts/news-map-reduce.yaml")
