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
          <div className="prose prose-sm max-w-none text-tone-secondary">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{helpContent}</ReactMarkdown>
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
