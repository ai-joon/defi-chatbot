from typing import Literal, Union, List


def create_lucene_query(
    terms: List[str], join_word: Literal["OR", "AND"], sub_query: bool = False
) -> Union[str, None]:
    if len(terms) == 0:
        return None

    escaped_terms = [
        term.replace("+", "\\+")
        .replace("-", "\\-")
        .replace("&&", "\\&&")
        .replace("||", "\\||")
        .replace("!", "\\!")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("^", "\\^")
        .replace('"', '\\"')
        .replace("~", "\\~")
        .replace("*", "\\*")
        .replace("?", "\\?")
        .replace(":", "\\:")
        .replace("/", "\\/")
        for term in terms
    ]

    if sub_query:
        return f'({f" {join_word} ".join(escaped_terms)})'

    return f" {join_word} ".join(escaped_terms)
