import { type AgentState, type TrackReference } from '@livekit/components-react';

import { cn } from '@/lib/utils';

import { HostawayVisualizer } from './hostaway-visualizer';

interface AgentAudioTileProps {
  state: AgentState;
  audioTrack: TrackReference;
  className?: string;
}

export const AgentTile = ({
  state,
  audioTrack,
  className,
  ref,
}: React.ComponentProps<'div'> & AgentAudioTileProps) => {
  return (
    <div ref={ref} className={cn('flex items-center justify-center', className)}>
      <HostawayVisualizer state={state} trackRef={audioTrack} className="w-full" />
    </div>
  );
};
