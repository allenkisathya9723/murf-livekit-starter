import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Activity, ShieldCheck, Languages, MicOff, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

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
      const errorMsg = 'Microphone access denied. Please click the lock icon in your browser address bar to allow microphone access.';
      setMicError(errorMsg);
      toast.error('Microphone Access Blocked', {
        description: 'Please enable microphone access in your browser settings to speak with JanMitra.',
        duration: 8000,
      });
    }
  };
  return (
    <div ref={ref} className="flex flex-col items-center justify-center p-4 w-full h-full overflow-hidden">
      <section className="bg-card text-card-foreground flex flex-col md:flex-row items-center justify-center rounded-3xl p-6 md:p-8 max-w-5xl w-full border shadow-lg mx-auto gap-8 md:gap-12">
        
        {/* Left Column: Image & Branding */}
        <div className="flex flex-col items-center text-center md:w-1/2">
          <div className="w-full max-w-sm mb-6 rounded-2xl overflow-hidden border border-emerald-100 shadow-sm bg-emerald-50">
             <img 
               src="/hero-asha.png" 
               alt="JanMitra ASHA Worker" 
               className="w-full h-auto object-cover aspect-video md:aspect-auto md:h-64" 
             />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2 tracking-tight">
            JanMitra (जनमित्र)
          </h1>
          <p className="text-muted-foreground text-sm font-medium">
            Aapka Swasthya Saathi
          </p>
        </div>

        {/* Right Column: Information & Actions */}
        <div className="flex flex-col w-full md:w-1/2 justify-center">
          
          {/* Condensed Features */}
          <div className="grid grid-cols-1 gap-3 mb-6">
            <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-xl border border-border/50">
              <ShieldCheck className="text-emerald-500 shrink-0" size={20} />
              <p className="text-sm font-medium">PM-JAY & Ayushman Bharat Guidance</p>
            </div>
            <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-xl border border-border/50">
              <Activity className="text-emerald-500 shrink-0" size={20} />
              <p className="text-sm font-medium">Find PHC, CHC, or Hospitals easily</p>
            </div>
          </div>

          {/* Condensed Languages */}
          <div className="w-full bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl p-3 mb-6 border border-emerald-100 dark:border-emerald-900/30">
            <div className="flex items-center gap-2 mb-2 text-emerald-700 dark:text-emerald-400 font-semibold text-xs">
              <Languages size={16} />
              <span>Speak Naturally:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {['Hindi', 'Telugu', 'Tamil', 'Malayalam', 'Bengali', 'Marathi', 'Kannada'].map((lang) => (
                <span key={lang} className="text-[10px] font-medium bg-background border px-2 py-1 rounded-full text-muted-foreground shadow-sm">
                  {lang}
                </span>
              ))}
            </div>
          </div>

          {/* Status & Start Button */}
          <div className="mb-4 flex items-center justify-start gap-2 text-sm font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/50 px-4 py-1.5 rounded-full border border-emerald-200 w-fit">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            Status: Ready
          </div>

          {micError && (
            <div className="mb-4 flex items-start gap-3 p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 rounded-xl text-red-700 dark:text-red-300 text-xs">
              <MicOff className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-red-800 dark:text-red-200">Microphone Blocked</p>
                <p className="mt-0.5">{micError}</p>
              </div>
            </div>
          )}

          <Button
            size="lg"
            onClick={handleStartCall}
            className="w-full rounded-full font-bold text-base px-8 py-6 bg-emerald-600 hover:bg-emerald-700 text-white shadow-md hover:shadow-lg transition-all"
          >
            {startButtonText}
          </Button>
        </div>

      </section>
    </div>
  );
};