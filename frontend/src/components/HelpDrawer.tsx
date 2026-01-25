import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

import helpContent from '../../../HELP.md?raw';
import helpUrl from '../../../HELP.md?url';

interface HelpDrawerProps {
  triggerLabel?: string;
}

export function HelpDrawer({ triggerLabel = 'Help' }: HelpDrawerProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <HelpCircle className="h-4 w-4" />
          <span>{triggerLabel}</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="flex h-full flex-col">
        <SheetHeader className="text-left">
          <SheetTitle>Help</SheetTitle>
          <SheetDescription>Quick guidance for getting the most out of each lesson.</SheetDescription>
        </SheetHeader>
        <ScrollArea className="mt-4 h-full pr-4">
          <div className="space-y-4">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h2 className="sr-only">{children}</h2>,
                h2: ({ children }) => (
                  <h2 className="pt-2 text-[0.7rem] font-semibold uppercase tracking-[0.2em] text-tone-tertiary">
                    {children}
                  </h2>
                ),
                p: ({ children }) => (
                  <p className="text-sm leading-relaxed text-tone-secondary">{children}</p>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal space-y-2 pl-5 text-sm text-tone-secondary">{children}</ol>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc space-y-2 pl-5 text-sm text-tone-secondary">{children}</ul>
                ),
                li: ({ children }) => <li className="pl-1">{children}</li>,
                a: ({ children, ...props }) => (
                  <a className="text-primary underline-offset-4 hover:underline" {...props}>
                    {children}
                  </a>
                ),
                strong: ({ children }) => <strong className="font-semibold text-tone-primary">{children}</strong>,
                code: ({ children }) => (
                  <code className="rounded bg-secondary/20 px-1.5 py-0.5 font-mono text-xs text-tone-primary">
                    {children}
                  </code>
                ),
              }}
            >
              {helpContent}
            </ReactMarkdown>
          </div>
          <div className="mt-6 text-sm">
            <a
              className="text-primary underline-offset-4 hover:underline"
              href={helpUrl}
              target="_blank"
              rel="noreferrer"
            >
              View full help in HELP.md
            </a>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
