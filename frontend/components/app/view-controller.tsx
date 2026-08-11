'use client';

import { useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';

import type { AppConfig } from '@/app-config';

import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({
  appConfig,
}: ViewControllerProps) {
  const session = useSessionContext();

  const { isConnected, start } = session;

  const { resolvedTheme } = useTheme();

  // Once the user starts a call, keep the session screen mounted.
  // This allows the Call Ended state to remain visible after disconnect.
  const [hasStarted, setHasStarted] = useState(false);

  // Start the LiveKit session.
  const handleStartCall = async () => {
    if (isConnected) {
      return;
    }

    setHasStarted(true);

    try {
      await start();
    } catch (error) {
      console.error(
        'Failed to start JanMitra session:',
        error
      );

      // If connection failed, return to the welcome screen.
      setHasStarted(false);
    }
  };

  return (
    <AnimatePresence mode="wait">
      {/* ================================================= */}
      {/* FIRST TIME / READY SCREEN */}
      {/* ================================================= */}

      {!hasStarted ? (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
        />
      ) : (
        /* ================================================= */
        /* SESSION SCREEN                                    */
        /* ================================================= */

        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={
            appConfig.isPreConnectBufferEnabled
          }

          audioVisualizerType={
            appConfig.audioVisualizerType
          }

          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }

          audioVisualizerColorShift={
            appConfig.audioVisualizerColorShift
          }

          audioVisualizerBarCount={
            appConfig.audioVisualizerBarCount
          }

          audioVisualizerGridRowCount={
            appConfig.audioVisualizerGridRowCount
          }

          audioVisualizerGridColumnCount={
            appConfig.audioVisualizerGridColumnCount
          }

          audioVisualizerRadialBarCount={
            appConfig.audioVisualizerRadialBarCount
          }

          audioVisualizerRadialRadius={
            appConfig.audioVisualizerRadialRadius
          }

          audioVisualizerWaveLineWidth={
            appConfig.audioVisualizerWaveLineWidth
          }

          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}