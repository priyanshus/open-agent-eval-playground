import logging

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from core.chatbot import Chatbot
from core.executor import Executor
from core.router import Router
from llm.client import create_llm_client
from tools.catalog import TOOL_CATALOG
from util.prompt_loader import get_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


def main() -> None:
    langfuse = get_client()
    langfuse_handler = CallbackHandler()
    llm = create_llm_client(callbacks=[langfuse_handler])

    router = Router()
    executor = Executor()
    chatbot = Chatbot(
        router=router,
        executor=executor,
        tool_catalog=TOOL_CATALOG,
        llm=llm,
        get_system_prompt=get_prompt,
    )

    sample_query = "Suggest me an itinerary for 1 day in Delhi?"
    with langfuse.start_as_current_observation(as_type="span", name="chatbot-request") as root:
        root.update_trace(input={"query": sample_query})
        response = chatbot.run(sample_query)
        root.update_trace(output={"response": response})

    print(response)
    langfuse.shutdown()


if __name__ == "__main__":
    main()
