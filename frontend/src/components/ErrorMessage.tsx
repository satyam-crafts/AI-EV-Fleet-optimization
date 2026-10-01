import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'An error occurred',
  message,
  onRetry,
}) => {
  return (
    <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-5 text-rose-200">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="h-6 w-6 text-rose-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-base font-semibold text-rose-300">{title}</h3>
          <p className="mt-1 text-sm text-rose-200/80">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center space-x-2 rounded-lg bg-rose-600/30 px-3 py-1.5 text-xs font-semibold text-rose-200 hover:bg-rose-600/50 transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry Request</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
