from langchain.schema.prompt_template import BasePromptTemplate
from langchain.llms.base import BaseLLM
from langchain.chains.combine_documents.map_reduce import MapReduceDocumentsChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain

from llms import llms

def load_map_reduce_chain(
    map_prompt: BasePromptTemplate,
    combine_prompt: BasePromptTemplate,
    map_llm: BaseLLM = llms["chatgpt16k"]["llm"],
    combine_llm: BaseLLM = llms["chatgpt16k"]["llm"],
    document_variable_name: str = "text",
    verbose: bool = False,
    combine_verbose: bool = False,
) -> MapReduceDocumentsChain:
    map_chain = LLMChain(llm=map_llm, prompt=map_prompt)
    combine_chain = LLMChain(
        llm=combine_llm, prompt=combine_prompt, verbose=combine_verbose
    )

    return MapReduceDocumentsChain(
        llm_chain=map_chain,
        combine_document_chain=StuffDocumentsChain(
            llm_chain=combine_chain,
            document_variable_name=document_variable_name,
            verbose=verbose,
        ),
        collapse_document_chain=StuffDocumentsChain(
            llm_chain=combine_chain,
            document_variable_name=document_variable_name,
            verbose=verbose,
        ),
        document_variable_name=document_variable_name,
        verbose=verbose,
    )