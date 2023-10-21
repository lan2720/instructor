import asyncio
from datetime import datetime
import enum
from instructor import OpenAISchema
from instructor.dsl import MultiTask

from pydantic import BaseModel, Field
from typing import Optional, List
import openai
import instructor

openai.api_base = "https://futu-002-caeast-001.openai.azure.com/"
openai.api_key = "5d050ffec2b94f5eb43c54c80149561e"
openai.api_version = "2023-07-01-preview"
openai.api_type = "azure"

# instructor.patch()

class SearchType(str, enum.Enum):
    VIDEO = "video"
    EMAIL = "email"

class Search(OpenAISchema):
    title: Optional[str] = Field(default=None, description="Title of the request")
    query: Optional[str] = Field(description="Query to search for relevant content")
    type: SearchType = Field(description="Type of search")
    
    async def execute(self):
        print(f"Searching for `{self.query}` using saerch_type named `{self.type}`")
        # print("当前正在执行", self.name, f"搜索类型: {self.type}")

# 原本此处是BaseModel现在换成OpenAISchema
# class MultiSearch(OpenAISchema):
#     tasks: List[Search]
MultiSearch = MultiTask(Search)
    # async def execute(self):
    #     return await asyncio.gather(*[search.execute() for search in self.searches])

def segment(data: str) -> MultiSearch:
    """segment是action, 接受到某个query时需要AI进行segment操作
        希望AI操作完返回MultiSearch的object, 然后就可以对这个object进行.execute()让多个query同时执行
    Args:
        data (str): _description_

    Returns:
        MultiSearch: _description_
    """
    completion = openai.ChatCompletion.create(
        engine="gpt-4",
        temperature=0.,
        functions=[MultiSearch.openai_schema],
        function_call={"name": MultiSearch.openai_schema["name"]},
        # response_model=MultiSearch,
        messages=[
            {"role": "system", 
             "content": "You are a helpful assistant."},
            {"role": "user", 
             "content": f"Consider the data below:\n{data} and segment it into multiple search queries"},
        ],
        max_tokens=1000
    )
    return MultiSearch.from_response(completion)

if __name__ == '__main__':
    query = "在youtube上播放今天的热门视频，然后，帮我发送一封生日祝福邮件给老板"
    query = "Please send me the video from last week about the investment case study and also documents about your GDPR policy?"
    queries = segment(query)
    # queries.execute()
    async def execute_queries(queries: MultiSearch):
        await asyncio.gather(*[q.execute() for q in queries.tasks])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(execute_queries(queries))
    loop.close()
