from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, AIMessage
from pydantic import ValidationError

from backend.nodes.base_node import BaseNode
from backend.schema.models import IntentOutput, State
from backend.util.prompt_loader import get_prompt


class UserIntentClassifier(BaseNode):
    def __init__(self, llm_client: BaseChatModel):
        super().__init__(llm_client)
        self._extract_user_intent_prompt = get_prompt("understand_intent_system")

    def __call__(self, state: State):
        messages = [
            SystemMessage(content=self._extract_user_intent_prompt),
            *state.messages
        ]
        structured_llm = self._llm_client.with_structured_output(IntentOutput)

        try:
            result: IntentOutput = structured_llm.invoke(messages)
            state.retry_count = state.retry_count + 1;

            if result.intent != "unknown" and result.confidence >= 0.6:
                return {
                    "intent": result.intent,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "clarification_question": result.clarification_question,
                }

            return {
                "intent": "unknown",
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "retry_count": state.retry_count,
                "messages": [
                    AIMessage(
                        content="I'm having trouble understanding your request. "
                                "Let's start fresh — could you describe your needs again?"
                    )
                ],
            }

        except ValidationError:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "reasoning": "Structured output validation failed",
                "clarification_question": "Could you clarify your request?",
                "retry_count": state.retry_count + 1,
                "messages": [
                    AIMessage(content="Could you clarify your request?")
                ],
            }

        except Exception as e:
            print("ACTUAL ERROR:", type(e), str(e))
            raise
