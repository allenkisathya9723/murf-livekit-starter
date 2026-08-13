'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Activity } from 'lucide-react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;

  supportsChatInput?: boolean;

  supportsVideoInput?: boolean;

  supportsScreenShare?: boolean;

  isPreConnectBufferEnabled?: boolean;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';

  audioVisualizerColor?: `#${string}`;

  audioVisualizerColorShift?: number;

  audioVisualizerBarCount?: number;

  audioVisualizerGridRowCount?: number;

  audioVisualizerGridColumnCount?: number;

  audioVisualizerRadialBarCount?: number;

  audioVisualizerRadialRadius?: number;

  audioVisualizerWaveLineWidth?: number;

  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,

  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();

  const { messages } = useSessionMessages(session);

  const [chatOpen, setChatOpen] = useState(false);

  const [isRestarting, setIsRestarting] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const { state: agentState } = useAgent();

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);

    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  /*
   * IMPORTANT:
   * We reload the frontend instead of calling session.start()
   * on an already-ended LiveKit session.
   *
   * This creates a completely fresh browser/session lifecycle.
   */
  const handleStartAgain = () => {
    if (isRestarting) {
      return;
    }

    setIsRestarting(true);

    window.location.reload();
  };

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      {/* Top fade */}
      <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />

      {/* Transcript */}
      <div className="absolute top-0 bottom-[135px] flex w-full flex-col md:bottom-[170px]">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
            >
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-40 md:[&>div>div]:px-6"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Main visualizer */}
      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />

      {/* Bottom area */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {/* Agent status */}
        <div className="mx-auto mb-6 flex justify-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${agentState}-${session.isConnected}`}
              initial={{
                opacity: 0,
                y: 5,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              exit={{
                opacity: 0,
                y: -5,
              }}
              className="bg-background/80 flex items-center gap-3 rounded-full border px-6 py-2.5 shadow-sm backdrop-blur-md"
            >
              {/* CONNECTING */}
              {agentState === 'connecting' || agentState === 'initializing' ? (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />

                    <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-500" />
                  </span>

                  <span className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                    Connecting...
                  </span>
                </>
              ) : /* LISTENING */
              agentState === 'listening' ? (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />

                    <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
                  </span>

                  <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                    Listening to you...
                  </span>
                </>
              ) : /* THINKING */
              agentState === 'thinking' ? (
                <>
                  <Activity className="h-4 w-4 animate-spin text-amber-500" />

                  <span className="text-sm font-semibold text-amber-700 dark:text-amber-400">
                    Thinking...
                  </span>
                </>
              ) : /* SPEAKING */
              agentState === 'speaking' ? (
                <>
                  <div className="flex h-3 items-center gap-1">
                    <span className="h-full w-1 animate-bounce rounded-full bg-emerald-500" />

                    <span className="h-2/3 w-1 animate-bounce rounded-full bg-emerald-500 delay-75" />

                    <span className="h-full w-1 animate-bounce rounded-full bg-emerald-500 delay-150" />
                  </div>

                  <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                    Agent is speaking...
                  </span>
                </>
              ) : /* CALL ENDED */
              !session.isConnected ? (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
                  </span>

                  <span className="text-sm font-semibold text-red-700 dark:text-red-400">
                    Call Ended
                  </span>

                  <Button
                    size="sm"
                    disabled={isRestarting}
                    onClick={handleStartAgain}
                    className="ml-2 rounded-full bg-emerald-600 px-4 text-white hover:bg-emerald-700"
                  >
                    {isRestarting ? 'Restarting...' : 'Start Again'}
                  </Button>
                </>
              ) : (
                /* CONNECTED */
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
                  </span>

                  <span className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                    Connected
                  </span>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Controls */}
        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />

          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
