"""Featherless client -- google/medgemma-27b-text-it.  [OWNER: B]

OpenAI-compatible, so one line:

    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="google/medgemma-27b-text-it",
                     base_url="https://api.featherless.ai/v1",
                     api_key=os.environ["FEATHERLESS_API_KEY"])

Text reasoning ONLY. MedGemma has no dental imaging in its training
distribution -- it answers confidently and wrongly about teeth (plan.md §3).
Warm it before every rehearsal.
"""
