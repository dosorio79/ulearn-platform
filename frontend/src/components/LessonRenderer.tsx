import { Target, Clock, RotateCcw, Copy, Download, Check } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { LessonSection } from './LessonSection';
import { LessonResponse } from '@/types/lesson';
import { buildLessonFilename, lessonToNotebook } from '@/lib/notebook';

interface LessonRendererProps {
  lesson: LessonResponse;
  onReset: () => void;
}

export function LessonRenderer({ lesson, onReset }: LessonRendererProps) {
  const [feedback, setFeedback] = useState<'yes' | 'no' | null>(null);
  const [copied, setCopied] = useState(false);

  const buildLessonMarkdown = () => {
    const lines: string[] = [];
    lines.push(`# ${lesson.objective}`);
    lines.push('');
    lines.push(`Total time: ${lesson.total_minutes} minutes`);
    lines.push('');
    for (const section of lesson.sections) {
      lines.push(`## ${section.title} (${section.minutes} min)`);
      lines.push(section.content_markdown.trim());
      lines.push('');
    }
    return lines.join('\n');
  };

  const handleCopyLesson = async () => {
    await navigator.clipboard.writeText(buildLessonMarkdown());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadLesson = () => {
    const blob = new Blob([buildLessonMarkdown()], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = buildLessonFilename(lesson, 'md');
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const handleDownloadNotebook = () => {
    const notebook = lessonToNotebook(lesson);
    const blob = new Blob([JSON.stringify(notebook, null, 2)], {
      type: 'application/x-ipynb+json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = buildLessonFilename(lesson, 'ipynb');
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-3xl mx-auto" data-testid="lesson-content">
      {/* Lesson Header */}
      <div className="mb-8 p-6 rounded-xl bg-card border border-border shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-primary/10">
            <Target className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-foreground mb-2">Learning Objective</h2>
            <p className="text-muted-foreground leading-relaxed">{lesson.objective}</p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>Total time: <strong className="text-foreground">{lesson.total_minutes} minutes</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleCopyLesson} className="gap-2">
              {copied ? <Check className="h-4 w-4 text-primary" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Copied' : 'Copy markdown'}
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadLesson} className="gap-2">
              <Download className="h-4 w-4" />
              Download .md
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownloadNotebook} className="gap-2">
              <Download className="h-4 w-4" />
              Download .ipynb
            </Button>
            <Button variant="outline" size="sm" onClick={onReset} className="gap-2">
              <RotateCcw className="h-4 w-4" />
              New lesson
            </Button>
          </div>
        </div>
      </div>

      {/* Lesson Sections */}
      <div className="p-6 rounded-xl bg-card border border-border shadow-sm">
        {lesson.sections.map((section) => (
          <LessonSection key={section.id} section={section} />
        ))}

        <div className="mt-8 border-t border-border pt-6 flex flex-col gap-3 text-sm text-muted-foreground">
          <p className="text-foreground font-medium">Was this lesson useful?</p>
          <div className="flex gap-3">
            <Button
              variant={feedback === 'yes' ? 'default' : 'outline'}
              size="sm"
              className="gap-2"
              onClick={() => setFeedback('yes')}
              aria-pressed={feedback === 'yes'}
            >
              👍 Yes
            </Button>
            <Button
              variant={feedback === 'no' ? 'default' : 'outline'}
              size="sm"
              className="gap-2"
              onClick={() => setFeedback('no')}
              aria-pressed={feedback === 'no'}
            >
              👎 Not really
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
