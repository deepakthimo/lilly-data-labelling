import requests
import json
import re
import asyncio

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
try:
    chat_llm = ChatOpenAI(model="gpt-5-mini-2025-08-07", temperature=0.0)
except Exception as e:
    print(f"[INITIALIZING LLM] Warning: Failed to initialize OpenAI clients. Check OPENAI_API_KEY. {e}", "node_error")
    # Initialize with a dummy object if the key is missing to prevent crash
    chat_llm = None

SYSTEM_INSTRUCTION = """You are an intelligent data extraction assistant specialized in structuring clinical document metadata.

YOUR GOAL:
Convert the provided "Table of Contents" raw text into a structured JSON dictionary.

INPUT FORMAT:
You will receive text where lines may contain section numbers, section titles, and occasionally trailing page numbers or visual separators (dots).

OUTPUT FORMAT:
Return ONLY a valid JSON object (dictionary) where:
- Keys: The Section Number (e.g., "1", "2.1", "10.3.1"). 
- Values: The Section Title (e.g., "Introduction", "Inclusion Criteria").

RULES FOR EXTRACTION:
1. IDENTIFY KEYS: Look for lines starting with a numeric sequence (e.g., "1.", "1.1", "6.2.3"). This number is your JSON Key. 
   - If a line starts with "Appendix X", treat "Appendix X" or the associated number (if present, e.g. "10.1") as the key.
2. CLEAN VALUES: 
   - Remove the section number from the title.
   - Remove any trailing page numbers (e.g., " 12", " 145") at the end of the line.
   - Remove visual separators like "......" or " . . . ".
3. MERGE WRAPPED LINES: If a line seems incomplete or acts as a continuation of the previous title, merge it into the previous value.
4. UNNUMBERED SECTIONS: If a section is important (like "SYNOPSIS" or "REFERENCES") but has no number, do not invent a number. Use the Title itself as the Key (e.g., "SYNOPSIS": "Synopsis").
5. ACCURACY: Do not summarize. Copy the exact text of the title.

EXAMPLE INPUT:
1. INTRODUCTION ... 12
1.1 Medical Background 12
2. STUDY OBJECTIVES
AND ENDPOINTS ... 15
10.1 Appendix 1: Laboratory Tests

EXAMPLE OUTPUT:
{
  "1": "Introduction",
  "1.1": "Medical Background",
  "2": "Study Objectives and Endpoints",
  "10.1": "Appendix 1: Laboratory Tests"
}
"""

async def personal_call_llm_for_toc_extraction(toc_content: str) -> str:
    """
    Asynchronously parses TOC text into structured JSON using system instructions.
    """

    user_prompt_template = PromptTemplate(
        input_variables=["toc_content"],
        template=(
            "Here is the cleaned Table of Contents text. "
            "Please parse this into JSON format obeying the rules above:\n\n"
            "{toc_content}"
        ),
    )

    human_prompt = user_prompt_template.format(toc_content=toc_content)

    messages = [
        SystemMessage(content=SYSTEM_INSTRUCTION),
        HumanMessage(content=human_prompt),
    ]

    response = await chat_llm.ainvoke(messages)
    import ast
    
    return ast.literal_eval(response.content)

async def cortex_call_llm_for_toc_extraction(prompt: str, cookie: str, max_retries: int = 2) -> dict:
    """
    Sends the cleaned TOC text to the Cortex LLM to get structured JSON.
    Uses POST to handle large payloads.
    """
    
    url = "https://cortex.lilly.com/model/ask/toc-structured-extractor"
    # 2. CONFIGURATION
    # These control the model behavior
    params = {
    "q": prompt,
    "stream": "false",
    "no_summary": "false",
    "workflow_timeout": 2600,
    "background_job": "false"
    }

    headers = {
        "accept": "application/json",
        "cookie": cookie,
    }

    # 3. RETRY LOOP
    for attempt in range(max_retries + 1):
        try:
            print(f"   -> LLM Request Attempt {attempt + 1}...")
            
            # Use run_in_executor to prevent 'requests' from blocking the async loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, params=params, headers=headers)

            )
            
            response.raise_for_status()

            # 4. PARSE RESPONSE
            result = response.json()
            raw_message = result.get('message', '')

            if not raw_message:
                print("      -> Warning: Received empty message from API.")
                raise json.JSONDecodeError("Empty message", "", 0)

            # 5. CLEAN MARKDOWN (```json ... ```)
            pattern = r"^```(?:json)?\s*(.*?)\s*```$"
            match = re.search(pattern, raw_message, re.DOTALL | re.IGNORECASE)
            
            if match:
                cleaned_json_str = match.group(1)
            else:
                cleaned_json_str = raw_message

            # 6. RETURN DICT
            return json.loads(cleaned_json_str)

        except json.JSONDecodeError as e:
            print(f"      -> JSON Parse Error: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2)  # Non-blocking sleep
            else:
                print("      -> All retries failed.")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"      -> API/Network Error: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2)
            else:
                return {}
        except Exception as e:
            print(f"      -> Unexpected Error: {e}")
            return {}
                
    return {}



if __name__ == "__main__":
    
    sample_prompt = """1. INTRODUCTION ... 12
1.1 Medical Background 12
2. STUDY OBJECTIVES
AND ENDPOINTS ... 15
10.1 Appendix 1: Laboratory Tests"""

    cookie = "CassieGuid_a363400f-dda7-4d1b-8731-df252632081a=17302b84-75b9-4212-bd4a-ec24d231cd05; consent_func_cookie=true; consent_performance=true; consent_adv_and_mark=true; _gcl_au=1.1.181415336.1763017471; CassieCookieFormConsent_a363400f-dda7-4d1b-8731-df252632081a=s9087c9067-1.s9105c9085-1.s9104c9084-1.s9123c9103-1.s9154c9134-1.s9155c9135-1.s9097c9077-1.s9099c9079-1.s9130c9110-1.s9089c9069-1.s9088c9068-1.s9143c9123-1.s9103c9083-1.s9142c9122-1.s9095c9075-1.s9096c9076-1.s9131c9111-1.s9138c9118-1.s9106c9086-1.s9107c9087-1.s9108c9088-1.s9109c9089-1.s9116c9096-1.s9140c9120-1.s9117c9097-1.s9137c9117-1.s9135c9115-1.s9118c9098-1.s9100c9080-1.s9132c9112-1.s9120c9100-1.s9134c9114-1.s9133c9113-1.s9136c9116-1.s9129c9109-1.s9139c9119-1.s9124c9104-1.s9125c9105-1.s9128c9108-1.s9141c9121-1.s9144c9124-1.s9145c9125-1.s9146c9126-1.s9147c9127-1.s9148c9128-1.s9152c9132-1.s9153c9133-1.s9156c9136-1.s9157c9137-1.s9158c9138-1.s9159c9139-1.s9160c9140-1.s9161c9141-1.s9163c9143-1.s9164c9144-1; CassieCookiePrivacyLink_a363400f-dda7-4d1b-8731-df252632081a=1; CassieCookieConsentDate_a363400f-dda7-4d1b-8731-df252632081a=1763017438188.4043; SyrenisGuid_a363400f-dda7-4d1b-8731-df252632081a=17302b84-75b9-4212-bd4a-ec24d231cd05; SyrenisCookieFormConsent_a363400f-dda7-4d1b-8731-df252632081a=s9087c9067-1.s9105c9085-1.s9104c9084-1.s9123c9103-1.s9154c9134-1.s9155c9135-1.s9097c9077-1.s9099c9079-1.s9130c9110-1.s9089c9069-1.s9088c9068-1.s9143c9123-1.s9103c9083-1.s9142c9122-1.s9095c9075-1.s9096c9076-1.s9131c9111-1.s9138c9118-1.s9106c9086-1.s9107c9087-1.s9108c9088-1.s9109c9089-1.s9116c9096-1.s9140c9120-1.s9117c9097-1.s9137c9117-1.s9135c9115-1.s9118c9098-1.s9100c9080-1.s9132c9112-1.s9120c9100-1.s9134c9114-1.s9133c9113-1.s9136c9116-1.s9129c9109-1.s9139c9119-1.s9124c9104-1.s9125c9105-1.s9128c9108-1.s9141c9121-1.s9144c9124-1.s9145c9125-1.s9146c9126-1.s9147c9127-1.s9148c9128-1.s9152c9132-1.s9153c9133-1.s9156c9136-1.s9157c9137-1.s9158c9138-1.s9159c9139-1.s9160c9140-1.s9161c9141-1.s9163c9143-1.s9164c9144-1; SyrenisCookiePrivacyLink_a363400f-dda7-4d1b-8731-df252632081a=1; SyrenisCookieConsentDate_a363400f-dda7-4d1b-8731-df252632081a=1763017438188.4043; _hp2_id.2107351403=%7B%22userId%22%3A%226939427928271759%22%2C%22pageviewId%22%3A%221904598763340643%22%2C%22sessionId%22%3A%223243986376366496%22%2C%22identity%22%3Anull%2C%22trackerVersion%22%3A%224.0%22%7D; _ga_2SFV35EN3H=GS2.1.s1763020400$o2$g0$t1763020400$j60$l0$h0; _ga=GA1.1.285424548.1763017471; _ga_WKTRG6FDF2=GS2.1.s1764155197$o2$g0$t1764155197$j60$l0$h0; _ga_F4QPGPB1JD=GS2.1.s1764308936$o1$g1$t1764309053$j49$l0$h0; AWSELBAuthSessionCookie-0=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; AWSELBAuthSessionCookie-1=XQe6v8hk3p8KlG4F4yu5mEepdYe6UvCET1/v1xkZZPDfaeSQI9wzOxSQsObqpFWgXEyMyP68EA6kLM2S3qm6kHidxnRpfMll1vLF5qWb5+eZ4d3gE/95ZK6VDjTfs8GNUG2pVXNwo2ly54XAbQY5R0AaLxYWhs1AOTrU+GVAriq8geVJicrY6T1V8phzUlE+fh6cqIG/UMvgv6QToVH/R2XLI+jHnpvSw5JLriwMx9I2dFO+9Q1AZzMH+NUqR+8Cg7LCBTJZ0KFUYC7aWl5SaCNFKTVYfI6eyy+29vFZS/00Nyh9+qN0Tpg7bFNQPSPovD+gYqGPPXfFpoS6unqrdHFMbxbmm5AC5dNJzi3AjxKnXN/TYBDCK6EdVx0jJBlpMPUlryzmSOQzdkWV9C903FJZe9JH0UzYV9w7y06KPYKpDPQTOfulTg5RVUbLGax/74HpJWXDEjyza4k6ZiyMsc5kpps9Hg550ZGD/bGxovUyQgkyh6Xc9pGVmM6p/qTGB3+FmaU+annwDSaE1kgL0hv2/z2s3VXI4SllFvcSbyBxF3vQKAAFAMsCgkAI7DS5tY1wPN91oC376otetLA7tA4oT6Lbj22c2QYmooJj/8xaK6c6mf4Ds4v9nno7StX/Hp67lOTYA14SFJnXzkZeSE0j/rTJWvL6bzS1JtgQ6scbwQeOPy/9/a0SEHFi+kUaTaLIjV0UQTruTcx8EfcKi7AQr/8eJ/QJuFd3beX2eXtqKFgrST8IO6lbyyL7fJqtUiFFfOXvPkh7Ys4ARgaJuCBLWAssq3y3oPcgwBxMtdzhdxaZ1NpM2m9ZsB1VTprd66nAx0IQUj5eSbfwR5DJZ354NcVnvin7Ex0YvI5VK2eFZCWD12p+AZFY7NWIM+YtV+Iqfy8sMtigBA7qUculZV9YiIkqSeWt227K5YrQgW9XHDSFDVKBxD4Xj3zg2Q0gbDdKf61QdH/GtoEBcBq2Se6MWv1SGI3kMdbuk7SYwSnFEObApluN/alpHLTTUxJmwX9Gjd+sJDwL+qQet8mX6oCdAIYMMjLHBaPKmB6A8olAiw4ReG0raQAxTdWfrOgs5M/SlS9+BUC+ebKmhWkCGSzSMu7p5j87fXjDGxt3qgnkMvLyKibIw+ZpBaEW48IJMbKPYpWFLtaQr4R5IogRn4tDyp2DSWVVRmCgB5w2BD1NwPMTd5DD9HNI2IL3aLRd66PNsLAs2kh+elmzxt70eilNyVz7d+rppOzj"

    #structured_output = asyncio.run(cortex_call_llm_for_toc_extraction(sample_prompt, cookie))
    #structured_output = call_llm_for_toc_extraction(sample_prompt, cookie)
    structured_output = asyncio.run(personal_call_llm_for_toc_extraction(sample_prompt))
    print(type(structured_output))
    print(json.dumps(structured_output, indent=2))