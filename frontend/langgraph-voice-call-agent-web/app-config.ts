import type { AppConfig } from './lib/types';

export const APP_CONFIG_DEFAULTS: AppConfig = {
  appName: 'STR Property Manager',
  pageTitle: 'STR Property Management Assistant',
  pageDescription:
    'AI-powered short-term rental management — portfolio analytics, market research, and owner communications via voice or chat',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/angryUnicorn.png',
  accent: '#002cf2',
  logoDark: '/angryUnicorn.png',
  accentDark: '#1fd5f9',
  startButtonText: 'Start Voice Call',
  startChatButtonText: 'Start Chat',

  agentName: undefined,
};
