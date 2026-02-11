"""
LangGraphAdapter bridges LiveKit Agents' LLM interface to a LangGraph workflow.

Key ideas:
- We stream LangGraph outputs using stream_mode=["messages", "custom"].
- "messages" chunks are converted to LiveKit llm.ChatChunk with ChoiceDelta(content=str).
- "custom" chunks support simple events like {"type": "say", data: {content: str}}.

References:
- LiveKit Agents LLM API (ChatChunk, ChoiceDelta): docs/livekit/agents (repo README and llm module)
- LangGraph streaming modes: messages/custom and astream():
  https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/streaming.md
- RemoteGraph astream usage:
  https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/use-remote-graph.md
"""

from typing import Any, Optional
import base64
from httpx import HTTPStatusError
from livekit.agents import llm
from livekit.agents.types import (
    APIConnectOptions,
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)
from livekit.agents.utils import shortuuid
from livekit.agents.llm.tool_context import FunctionTool, RawFunctionTool, ToolChoice
from livekit.agents.utils.images import encode, EncodeOptions
try:
    # Prefer concrete ImageContent class if available
    from livekit.agents.llm import ImageContent as LKImageContent  # type: ignore
except Exception:  # pragma: no cover
    LKImageContent = None  # sentinel; we'll fallback to hasattr checks
from langgraph.pregel import Pregel
from langchain_core.messages import BaseMessageChunk, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import Command
from langgraph.errors import GraphInterrupt
from langgraph.pregel.remote import RemoteException

import logging

logger = logging.getLogger(__name__)


class LangGraphStream(llm.LLMStream):
    """LLMStream implementation that proxies a LangGraph stream.

    - Creates LiveKit ChatChunks from LangGraph "messages" stream chunks.
    - Passes through simple custom events (e.g., "say") from LangGraph "custom" stream.

    See:
      - LangGraph stream modes: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/streaming.md
      - LiveKit LLM stream contract: livekit.agents.llm.LLMStream (in repo)
    """

    def __init__(
        self,
        llm: llm.LLM,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool | RawFunctionTool],
        conn_options: APIConnectOptions,
        graph: Pregel,
    ):
        super().__init__(llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._graph = graph

    async def _run(self):
        """Consume LangGraph stream and emit LiveKit ChatChunks."""
        # Determine input for LangGraph:
        # - If a checkpoint exists, send ONLY the new user message (LangGraph
        #   loads prior state from its checkpoint automatically).
        # - If no checkpoint, send the full ChatContext (first turn).
        chat_state = self._chat_ctx_to_state()

        try:
            current_state = await self._graph.aget_state(config=self._llm._config)
            if current_state and current_state.values and "messages" in current_state.values:
                # Checkpoint exists — clean up incomplete tool calls if needed
                messages = current_state.values["messages"]
                cleaned_messages = self._clean_incomplete_tool_calls(messages)

                has_incomplete_tool_calls = any(
                    isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls
                    for msg in messages
                )
                cleaned_has_incomplete = any(
                    isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls
                    for msg in cleaned_messages
                )

                if has_incomplete_tool_calls and not cleaned_has_incomplete:
                    logger.info("Cleaned incomplete tool calls, updating LangGraph state")
                    try:
                        await self._graph.aupdate_state(
                            config=self._llm._config,
                            values={"messages": cleaned_messages}
                        )
                        logger.debug("Updated LangGraph state with cleaned messages")
                    except Exception as update_error:
                        logger.warning(f"Could not update LangGraph state: {update_error}.")

                # Checkpoint exists → send only the NEW user message.
                # LangGraph's add_messages reducer appends it to the checkpoint.
                new_user_msgs = [
                    m for m in chat_state.get("messages", [])
                    if isinstance(m, HumanMessage)
                ]
                last_user = new_user_msgs[-1] if new_user_msgs else None
                if last_user:
                    state = {"messages": [last_user]}
                    logger.debug(
                        f"Checkpoint has {len(cleaned_messages)} msgs; sending new user message to LangGraph"
                    )
                else:
                    # Fallback: no user message found in ChatContext
                    state = chat_state
                    logger.warning("Checkpoint exists but no new user message in ChatContext; sending full context")
            else:
                # No checkpoint yet (first turn) — send full ChatContext
                state = chat_state
                logger.debug("No LangGraph checkpoint, using full ChatContext")
        except Exception as e:
            logger.warning(f"Could not get state from LangGraph, using ChatContext: {e}")
            state = chat_state

        # see if we need to respond to an interrupt (resume)
        if interrupt := await self._get_interrupt():
            used_messages = [AIMessage(interrupt.value)]
            # resume with last user content if any
            last_user = next(
                (m for m in reversed(state.get("messages", [])) if isinstance(m, HumanMessage)),
                None,
            )
            if last_user:
                used_messages.append(last_user)
                input_state = Command(resume=(last_user.content, used_messages))
            else:
                input_state = Command(resume=(interrupt.value, used_messages))
        else:
            input_state = state

        try:
            # LangGraph astream with explicit modes (messages, custom)
            # https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/streaming.md
            async for mode, data in self._graph.astream(
                input_state, config=self._llm._config, stream_mode=["messages", "custom"]
            ):
                if mode == "messages":
                    if data and len(data) > 0:
                        message = data[0]
                        msg_type = type(message).__name__
                        msg_content_preview = ""
                        if hasattr(message, "content"):
                            c = message.content
                            msg_content_preview = (str(c)[:80] + "...") if len(str(c)) > 80 else str(c)
                        elif isinstance(message, dict):
                            c = message.get("content", "")
                            msg_content_preview = (str(c)[:80] + "...") if len(str(c)) > 80 else str(c)
                        logger.debug(f"Stream message: type={msg_type} content_preview={msg_content_preview!r}")
                        if not self._should_emit_message(message):
                            continue
                        if chunk := await self._to_livekit_chunk(message):
                            self._event_ch.send_nowait(chunk)

                if mode == "custom":
                    # Minimal custom protocol: {"type": "say", data: {content: str}}
                    if isinstance(data, dict) and (event := data.get("type")):
                        if event in ("say"):
                            content = (data.get("data") or {}).get("content")
                            if chunk := await self._to_livekit_chunk(content):
                                self._event_ch.send_nowait(chunk)
        except RemoteException as remote_exc:
            # Handle LangGraph remote errors (e.g., incomplete tool calls)
            error_data = remote_exc.data if hasattr(remote_exc, 'data') else {}
            error_message = error_data.get('message', str(remote_exc)) if isinstance(error_data, dict) else str(remote_exc)
            
            if 'tool_calls' in error_message.lower() and 'ToolMessage' in error_message:
                # Incomplete tool calls error - try to fix by updating state and retrying
                logger.warning(f"Incomplete tool calls detected: {error_message}")
                logger.info("Attempting to fix by updating LangGraph state with cleaned messages")
                
                try:
                    # Strategy: Use a NEW thread_id to completely avoid the corrupted state
                    # This is more reliable than trying to update the existing state
                    logger.info("Creating new thread_id to avoid corrupted state with incomplete tool calls")
                    import uuid
                    new_thread_id = str(uuid.uuid4())
                    new_config = {
                        **self._llm._config,
                        "configurable": {
                            **self._llm._config.get("configurable", {}),
                            "thread_id": new_thread_id
                        }
                    }
                    logger.info(f"Using new thread_id {new_thread_id} to start fresh")
                    
                    # Get current state and clean it, but use it with the NEW thread_id
                    current_state = await self._graph.aget_state(config=self._llm._config)
                    if current_state and current_state.values and "messages" in current_state.values:
                        messages = current_state.values["messages"]
                        cleaned_messages = self._clean_incomplete_tool_calls(messages)
                        
                        # Use cleaned messages with new thread_id (fresh state)
                        cleaned_state = {"messages": cleaned_messages}
                        
                        # Update the new thread's state with cleaned messages
                        try:
                            await self._graph.aupdate_state(
                                config=new_config,
                                values={"messages": cleaned_messages}
                            )
                            logger.debug("Updated new thread state with cleaned messages")
                        except Exception as update_error:
                            logger.warning(f"Could not update new thread state: {update_error}. Will use cleaned state directly.")
                        
                        if interrupt := await self._get_interrupt():
                            # Handle interrupt case
                            used_messages = [AIMessage(interrupt.value)]
                            last_user = next(
                                (m for m in reversed(cleaned_messages) if isinstance(m, HumanMessage)),
                                None,
                            )
                            if last_user:
                                used_messages.append(last_user)
                                retry_state = Command(resume=(last_user.content, used_messages))
                            else:
                                retry_state = Command(resume=(interrupt.value, used_messages))
                        else:
                            retry_state = cleaned_state
                        
                        # Retry the stream with NEW thread_id
                        async for mode, data in self._graph.astream(
                            retry_state, config=new_config, stream_mode=["messages", "custom"]
                        ):
                            if mode == "messages":
                                if data and len(data) > 0:
                                    message = data[0]
                                    if not self._should_emit_message(message):
                                        continue
                                    if chunk := await self._to_livekit_chunk(message):
                                        self._event_ch.send_nowait(chunk)
                            elif mode == "custom":
                                if isinstance(data, dict) and (event := data.get("type")):
                                    if event in ("say"):
                                        content = (data.get("data") or {}).get("content")
                                        if chunk := await self._to_livekit_chunk(content):
                                            self._event_ch.send_nowait(chunk)
                        # Update the adapter's config to use the new thread_id for future calls
                        self._llm._config = new_config
                        return  # Successfully retried
                    else:
                        # No state exists, just use new thread_id with ChatContext
                        logger.info("No existing state, using ChatContext with new thread_id")
                        fallback_state = self._chat_ctx_to_state()
                        async for mode, data in self._graph.astream(
                            fallback_state, config=new_config, stream_mode=["messages", "custom"]
                        ):
                            if mode == "messages":
                                if data and len(data) > 0:
                                    message = data[0]
                                    if not self._should_emit_message(message):
                                        continue
                                    if chunk := await self._to_livekit_chunk(message):
                                        self._event_ch.send_nowait(chunk)
                            elif mode == "custom":
                                if isinstance(data, dict) and (event := data.get("type")):
                                    if event in ("say"):
                                        content = (data.get("data") or {}).get("content")
                                        if chunk := await self._to_livekit_chunk(content):
                                            self._event_ch.send_nowait(chunk)
                        self._llm._config = new_config
                        return
                except Exception as fix_error:
                    logger.error(f"Failed to fix incomplete tool calls: {fix_error}")
                    # Last resort: Use ChatContext with a NEW thread_id to avoid the corrupted state
                    logger.warning("Falling back to ChatContext with new thread_id to avoid incomplete tool call error")
                    
                    # Create a new config with a different thread_id to start fresh
                    import uuid
                    new_thread_id = str(uuid.uuid4())
                    fallback_config = {
                        **self._llm._config,
                        "configurable": {
                            **self._llm._config.get("configurable", {}),
                            "thread_id": new_thread_id
                        }
                    }
                    logger.info(f"Using new thread_id {new_thread_id} to avoid corrupted state")
                    
                    fallback_state = self._chat_ctx_to_state()
                    try:
                        async for mode, data in self._graph.astream(
                            fallback_state, config=fallback_config, stream_mode=["messages", "custom"]
                        ):
                            if mode == "messages":
                                if data and len(data) > 0:
                                    message = data[0]
                                    if not self._should_emit_message(message):
                                        continue
                                    if chunk := await self._to_livekit_chunk(message):
                                        self._event_ch.send_nowait(chunk)
                            elif mode == "custom":
                                if isinstance(data, dict) and (event := data.get("type")):
                                    if event in ("say"):
                                        content = (data.get("data") or {}).get("content")
                                        if chunk := await self._to_livekit_chunk(content):
                                            self._event_ch.send_nowait(chunk)
                    except RemoteException as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")
                        # Send an error message to the user
                        error_chunk = self._create_livekit_chunk(
                            "I'm sorry, there was an issue with the conversation state. Let's start fresh."
                        )
                        if error_chunk:
                            self._event_ch.send_nowait(error_chunk)
                    return
            else:
                # Other RemoteException - re-raise
                logger.error(f"LangGraph RemoteException: {error_message}")
                raise
        except GraphInterrupt:
            # Graph was interrupted; we gracefully stop streaming
            pass

        # If interrupted late, send the string as a message
        if interrupt := await self._get_interrupt():
            if chunk := await self._to_livekit_chunk(interrupt.value):
                self._event_ch.send_nowait(chunk)

    def _chat_ctx_to_state(self) -> dict[str, Any]:
        """Translate LiveKit ChatContext into LangGraph state messages.

        We map LiveKit roles to LangChain message classes (AIMessage/HumanMessage/SystemMessage).
        """
        messages: list[AIMessage | HumanMessage | SystemMessage] = []
        for item in getattr(self._chat_ctx, "items", []):
            if getattr(item, "type", None) != "message":
                continue
            role = getattr(item, "role", None)
            item_id = getattr(item, "id", None)

            # Prefer rich content if available, else fallback to text_content
            content_out: Any
            raw_content = getattr(item, "content", None)
            text_content = getattr(item, "text_content", None)

            if isinstance(raw_content, list) and raw_content:
                parts: list[dict[str, Any]] = []
                for c in raw_content:
                    if isinstance(c, str):
                        parts.append({"type": "text", "text": c})
                    elif (LKImageContent and isinstance(c, LKImageContent)) or hasattr(c, "image"):
                        img_obj = getattr(c, "image", None)
                        if isinstance(img_obj, str):
                            parts.append({"type": "image_url", "image_url": {"url": img_obj}})
                        else:
                            try:
                                img_bytes = encode(img_obj, EncodeOptions(format="JPEG"))
                                data_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"
                                parts.append({"type": "image_url", "image_url": {"url": data_url}})
                            except Exception:
                                logger.warning("Unsupported image in ChatContext; skipping image part")
                    else:
                        logger.warning("Unsupported content type in ChatContext message; skipping")
                content_out = parts if parts else (text_content or "")
            else:
                # Fallback to text only
                if not text_content:
                    continue
                content_out = text_content

            if role == "assistant":
                messages.append(AIMessage(content=content_out, id=item_id))
            elif role == "user":
                messages.append(HumanMessage(content=content_out, id=item_id))
            elif role in ["system", "developer"]:
                messages.append(SystemMessage(content=content_out, id=item_id))

        return {"messages": messages}

    async def _get_interrupt(self) -> Optional[str]:
        """Inspect graph state for latest assistant interrupt string.

        Uses Pregel.aget_state to retrieve interrupts from tasks.
        https://github.com/langchain-ai/langgraph/blob/main/docs/docs/reference/pregel.md
        """
        try:
            state = await self._graph.aget_state(config=self._llm._config)
            interrupts = [
                interrupt for task in state.tasks for interrupt in task.interrupts
            ]
            assistant = next(
                (
                    interrupt
                    for interrupt in reversed(interrupts)
                    if isinstance(interrupt.value, str)
                ),
                None,
            )
            return assistant
        except HTTPStatusError as e:
            logger.warning(f"HTTP error getting LangGraph state: {e}")
            return None
        except (TypeError, AttributeError, KeyError) as e:
            # Handle the case where state or checkpoint is None
            logger.warning(f"Error getting interrupt state: {e}")
            return None
        except Exception as e:
            # If we can't get state (e.g., LangGraph server not running), log and return None
            logger.warning(f"Could not get LangGraph state (server may not be running): {e}")
            return None

    def _to_message(cls, msg: llm.ChatMessage) -> HumanMessage:
        # Helper used for converting LiveKit inbound to HumanMessage
        if isinstance(msg.content, str):
            content = msg.content
        elif isinstance(msg.content, list):
            content = []
            for c in msg.content:
                if isinstance(c, str):
                    content.append({"type": "text", "text": c})
                elif (LKImageContent and isinstance(c, LKImageContent)) or hasattr(c, "image"):
                    img_obj = getattr(c, "image", None)
                    if isinstance(img_obj, str):
                        content.append({"type": "image_url", "image_url": {"url": img_obj}})
                    else:
                        try:
                            img_bytes = encode(img_obj, EncodeOptions(format="JPEG"))
                            data_url = f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode('utf-8')}"
                            content.append({"type": "image_url", "image_url": {"url": data_url}})
                        except Exception:
                            logger.warning("Unsupported image type; skipping")
                else:
                    logger.warning("Unsupported content type")
        else:
            content = ""

        return HumanMessage(content=content, id=msg.id)

    @staticmethod
    def _create_livekit_chunk(
        content: str,
        *,
        id: str | None = None,
    ) -> llm.ChatChunk | None:
        # ChoiceDelta.content must be a string
        return llm.ChatChunk(
            id=id or shortuuid(),
            delta=llm.ChoiceDelta(role="assistant", content=content),
        )

    @staticmethod
    async def _to_livekit_chunk(
        msg: BaseMessageChunk | str | None,
    ) -> llm.ChatChunk | None:
        """Normalize LangGraph message chunk or string into a ChatChunk.

        Accepts:
          - str content
          - message-like objects with .content (str)
          - dicts with {id?, content?}
          - lists where first element carries the content
        Returns None when content is missing or not a string.
        """
        if not msg:
            return None

        request_id = None
        content = msg

        if isinstance(msg, str):
            content = msg
        elif hasattr(msg, "content") and isinstance(msg.content, str):
            request_id = getattr(msg, "id", None)
            content = msg.content
        elif hasattr(msg, "content") and isinstance(msg.content, list):
            # Claude/Anthropic returns content as list of blocks:
            # [{"type": "text", "text": "..."}, ...]
            request_id = getattr(msg, "id", None)
            text_parts = []
            for block in msg.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "".join(text_parts)
        elif isinstance(msg, dict):
            request_id = msg.get("id")
            raw = msg.get("content")
            if isinstance(raw, str):
                content = raw
            elif isinstance(raw, list):
                # Claude/Anthropic returns content as list of blocks
                text_parts = []
                for block in raw:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "".join(text_parts)
            else:
                content = ""
        elif isinstance(msg, list):
            # Handle case where msg is a list - try to extract content from first item
            if msg and len(msg) > 0:
                first_item = msg[0]
                if isinstance(first_item, str):
                    content = first_item
                elif hasattr(first_item, "content") and isinstance(first_item.content, str):
                    content = first_item.content
                    request_id = getattr(first_item, "id", None)
                elif isinstance(first_item, dict):
                    content = first_item.get("content", "")
                    request_id = first_item.get("id")
                else:
                    logger.warning(f"Unsupported message type in list: {type(first_item)}")
                    return None
            else:
                logger.warning("Empty message list received")
                return None
        else:
            logger.warning(f"Unsupported message type: {type(msg)}")
            return None

        # Ensure content is a string
        if not isinstance(content, str):
            logger.warning(f"Content is not a string: {type(content)}")
            return None

        return LangGraphStream._create_livekit_chunk(content, id=request_id)
    
    @staticmethod
    def _should_emit_message(message) -> bool:
        """Return True if this LangGraph message chunk should be sent to TTS.

        Filters out:
        - ToolMessages (raw JSON tool results)
        - HumanMessages (echoed user input)
        - AIMessages that are tool calls (no text content)
        Only final AIMessage text tokens reach the voice pipeline.

        Handles both LangChain message objects and dicts (RemoteGraph
        may return deserialized dicts over HTTP).
        """
        # --- LangChain message objects ---
        if isinstance(message, (ToolMessage, HumanMessage)):
            logger.debug(f"Filtering out {type(message).__name__}")
            return False
        if isinstance(message, AIMessage):
            if getattr(message, 'tool_calls', None) or getattr(message, 'tool_call_chunks', None):
                logger.debug("Filtering out AIMessage with tool_calls")
                return False
            if not message.content:
                return False
            return True

        # --- Dict messages (RemoteGraph HTTP deserialization) ---
        if isinstance(message, dict):
            msg_type = message.get("type", "")
            if msg_type in ("tool", "ToolMessage", "ToolMessageChunk"):
                logger.debug(f"Filtering out dict message type={msg_type}")
                return False
            if msg_type in ("human", "HumanMessage", "HumanMessageChunk"):
                logger.debug(f"Filtering out dict message type={msg_type}")
                return False
            if msg_type in ("ai", "AIMessage", "AIMessageChunk"):
                if message.get("tool_calls") or message.get("tool_call_chunks"):
                    logger.debug("Filtering out dict AI message with tool_calls")
                    return False
                content = message.get("content", "")
                if not content:
                    return False
                # Also detect raw JSON content that slipped through
                if isinstance(content, str) and content.strip().startswith(("{", "[")):
                    logger.debug("Filtering out dict AI message with JSON content")
                    return False
            return True

        # For str and other types, emit
        return True

    @staticmethod
    def _clean_incomplete_tool_calls(messages: list) -> list:
        """Remove AIMessages with tool_calls that don't have corresponding ToolMessages.
        
        This prevents the 'incomplete tool calls' error when LangGraph validates state.
        If an AIMessage has tool_calls, we check if there are ToolMessages for each call.
        If not, we convert it to a regular AIMessage without tool_calls.
        """
        cleaned = []
        
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                # Check if all tool calls have corresponding ToolMessages
                tool_call_ids = []
                for tc in msg.tool_calls:
                    if isinstance(tc, dict):
                        tool_call_ids.append(tc.get('id'))
                    elif hasattr(tc, 'id'):
                        tool_call_ids.append(tc.id)
                
                # Look ahead to see if ToolMessages exist for all tool calls
                has_all_tool_messages = True
                for tc_id in tool_call_ids:
                    found = False
                    # Check remaining messages for ToolMessage with this tool_call_id
                    for future_msg in messages[i + 1:]:
                        if isinstance(future_msg, ToolMessage):
                            future_tool_call_id = getattr(future_msg, 'tool_call_id', None)
                            if future_tool_call_id == tc_id:
                                found = True
                                break
                    if not found:
                        has_all_tool_messages = False
                        break
                
                if has_all_tool_messages:
                    # All tool calls have ToolMessages, keep the AIMessage
                    cleaned.append(msg)
                else:
                    # Incomplete tool calls - convert to regular AIMessage without tool_calls
                    logger.warning(f"Removing incomplete tool calls from AIMessage to prevent state errors")
                    # Create a new AIMessage with just the content, no tool_calls
                    cleaned_msg = AIMessage(
                        content=msg.content or "Previous tool call was interrupted",
                        id=getattr(msg, 'id', None)
                    )
                    cleaned.append(cleaned_msg)
            elif isinstance(msg, ToolMessage):
                # Keep ToolMessages - they should have corresponding AIMessages
                # (If the AIMessage was removed above, this becomes orphaned but that's OK)
                cleaned.append(msg)
            else:
                # Regular message (HumanMessage, SystemMessage, etc.), keep it
                cleaned.append(msg)
        
        return cleaned


class LangGraphAdapter(llm.LLM):
    """Adapter that exposes a LangGraph agent as a LiveKit LLM.

    chat() creates a LangGraphStream that maps ChatContext + tools into
    the agent execution. Tools are passed through so LiveKit can advertise
    capabilities to the calling side when applicable.

    See LiveKit LLM.chat signature and LLMStream contract in the docs.
    """

    def __init__(self, graph: Any, config: dict[str, Any] | None = None):
        super().__init__()
        self._graph = graph
        self._config = config

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[FunctionTool | RawFunctionTool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> llm.LLMStream:
        """Create a streaming session backed by the provided LangGraph.

        - chat_ctx: prior conversation context from LiveKit
        - tools: tool definitions (forwarded to base stream for metadata)
        - conn_options: stream connection options
        """
        return LangGraphStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
            graph=self._graph,
        )