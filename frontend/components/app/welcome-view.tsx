import { useState } from 'react';
import { Activity, AlertCircle, Languages, MicOff, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [micError, setMicError] = useState<string | null>(null);

  const handleStartCall = async () => {
    setMicError(null);
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      onStartCall();
    } catch (err: any) {
      console.error('Microphone error:', err);
      const errorMsg =
        'Microphone access denied. Please click the lock icon in your browser address bar to allow microphone access.';
      setMicError(errorMsg);
      toast.error('Microphone Access Blocked', {
        description:
          'Please enable microphone access in your browser settings to speak with JanMitra.',
        duration: 8000,
      });
    }
  };
  return (
    <div
      ref={ref}
      className="flex h-full w-full flex-col items-center justify-center overflow-hidden p-4"
    >
      <section className="bg-card text-card-foreground mx-auto flex w-full max-w-5xl flex-col items-center justify-center gap-8 rounded-3xl border p-6 shadow-lg md:flex-row md:gap-12 md:p-8">
        {/* Left Column: Image & Branding */}
        <div className="flex flex-col items-center text-center md:w-1/2">
          <div className="mb-6 w-full max-w-sm overflow-hidden rounded-2xl border border-emerald-100 bg-emerald-50 shadow-sm">
            <img
              src="/hero-asha.png"
              alt="JanMitra ASHA Worker"
              className="aspect-video h-auto w-full object-cover md:aspect-auto md:h-64"
            />
          </div>
          <h1 className="mb-2 text-3xl font-bold tracking-tight md:text-4xl">JanMitra (जनमित्र)</h1>
          <p className="text-muted-foreground text-sm font-medium">Aapka Swasthya Saathi</p>
        </div>

        {/* Right Column: Information & Actions */}
        <div className="flex w-full flex-col justify-center md:w-1/2">
          {/* Condensed Features */}
          <div className="mb-6 grid grid-cols-1 gap-3">
            <div className="bg-muted/40 border-border/50 flex items-center gap-3 rounded-xl border p-3">
              <ShieldCheck className="shrink-0 text-emerald-500" size={20} />
              <p className="text-sm font-medium">PM-JAY & Ayushman Bharat Guidance</p>
            </div>
            <div className="bg-muted/40 border-border/50 flex items-center gap-3 rounded-xl border p-3">
              <Activity className="shrink-0 text-emerald-500" size={20} />
              <p className="text-sm font-medium">Find PHC, CHC, or Hospitals easily</p>
            </div>
          </div>

          {/* Condensed Languages */}
          <div className="mb-6 w-full rounded-xl border border-emerald-100 bg-emerald-50/50 p-3 dark:border-emerald-900/30 dark:bg-emerald-950/20">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
              <Languages size={16} />
              <span>Speak Naturally:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {['Hindi', 'Telugu', 'Tamil', 'Malayalam', 'Bengali', 'Marathi', 'Kannada'].map(
                (lang) => (
                  <span
                    key={lang}
                    className="bg-background text-muted-foreground rounded-full border px-2 py-1 text-[10px] font-medium shadow-sm"
                  >
                    {lang}
                  </span>
                )
              )}
            </div>
          </div>

          {/* Status & Start Button */}
          <div className="mb-4 flex w-fit items-center justify-start gap-2 rounded-full border border-emerald-200 bg-emerald-100 px-4 py-1.5 text-sm font-bold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
            </span>
            Status: Ready
          </div>

          {micError && (
            <div className="mb-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
              <MicOff className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
              <div>
                <p className="font-bold text-red-800 dark:text-red-200">Microphone Blocked</p>
                <p className="mt-0.5">{micError}</p>
              </div>
            </div>
          )}

          <Button
            size="lg"
            onClick={handleStartCall}
            className="w-full rounded-full bg-emerald-600 px-8 py-6 text-base font-bold text-white shadow-md transition-all hover:bg-emerald-700 hover:shadow-lg"
          >
            {startButtonText}
          </Button>
        </div>
      </section>
    </div>
  );
};
