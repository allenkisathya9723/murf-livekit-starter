'use client';

import { useMemo } from 'react';
import type { CSSProperties } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

function getOrGenerateUserId(): string {
  if (typeof window === 'undefined') {
    return '';
  }
  let userId = localStorage.getItem('janmitra_user_id');
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem('janmitra_user_id', userId);
  }
  return userId;
}

export function App({ appConfig }: AppProps) {
  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig);
    }

    return TokenSource.custom(async () => {
      const userId = getOrGenerateUserId();
      const res = await fetch('/api/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch token: ${res.statusText}`);
      }
      return await res.json();
    });
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />

      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController appConfig={appConfig} />
      </main>

      <div className="fixed top-6 left-1/2 z-50 -translate-x-1/2">
        <StartAudioButton
          label="🔊 Click to Unmute Agent Voice"
          variant="destructive"
          className="flex cursor-pointer items-center gap-2 rounded-full bg-indigo-600 px-6 py-3 font-semibold text-white shadow-2xl transition-all hover:bg-indigo-500"
        />
      </div>

      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
