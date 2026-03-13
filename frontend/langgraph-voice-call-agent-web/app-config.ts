import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  appName: 'FreeNow Booking Assistant',
  pageTitle: 'FreeNow Ride Booking Assistant',
  pageDescription:
    'AI-powered ride-hailing assistant — book rides and check booking status via voice or chat',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/angryUnicorn.png',
  accent: '#015478',
  logoDark: '/angryUnicorn.png',
  accentDark: '#ff0a2b',
  startButtonText: 'Start Voice Call',
  startChatButtonText: 'Start Chat',

  agentName: undefined,
};
