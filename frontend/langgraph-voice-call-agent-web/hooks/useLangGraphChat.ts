'use client';

import { useMemo } from 'react';

import type { Message } from '@langchain/langgraph-sdk';
import { useStream } from '@langchain/langgraph-sdk/react';
import type { ReceivedChatMessage } from '@livekit/components-react';

type UseLangGraphChatParams = {
  apiUrl?: string;
  assistantId?: string;
  messagesKey?: string;
};

type UseLangGraphChatResult = {
  messages: ReceivedChatMessage[];
  send: (text: string) => Promise<void>;
};

/**
 * Lightweight adapter around LangGraph useStream that presents
 * messages and send() in the same shape our chat UI expects.
 */
export default function useLangGraphChat(params: UseLangGraphChatParams): UseLangGraphChatResult {
  const { apiUrl, assistantId, messagesKey = 'messages' } = params;

  const stream = useStream<{ messages: Message[] }>({
    apiUrl,
    assistantId: assistantId ?? '',
    messagesKey,
  });

  const mappedMessages = useMemo<ReceivedChatMessage[]>(() => {
    const now = Date.now();
    return (stream.messages ?? []).map((m, idx) => {
      const isHuman = (m as any).type === 'human';
      const raw = (m as any).content;
      // content can be a string or an array of content blocks
      let text: string;
      if (typeof raw === 'string') {
        text = raw;
      } else if (Array.isArray(raw)) {
        text = raw
          .filter((block: any) => block.type === 'text')
          .map((block: any) => block.text)
          .join('');
      } else {
        text = raw != null ? String(raw) : '';
      }
      return {
        id: (m as any).id ?? `${now}-${idx}`,
        message: text,
        timestamp: now + idx,
        from: {
          identity: isHuman ? 'you' : 'agent',
          name: isHuman ? 'You' : 'Agent',
          isLocal: isHuman,
        } as any,
      } as unknown as ReceivedChatMessage;
    });
  }, [stream.messages]);

  async function send(text: string) {
    if (!text || !assistantId || !apiUrl) return;
    const newMessage = { type: 'human', content: text } as any;
    stream.submit({ messages: [newMessage] });
  }

  return { messages: mappedMessages, send };
}
