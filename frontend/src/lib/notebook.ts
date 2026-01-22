import type { LessonResponse } from '@/types/lesson';

type NotebookCell = {
  cell_type: 'markdown' | 'code';
  metadata: Record<string, unknown>;
  source: string[];
  execution_count?: number | null;
  outputs?: unknown[];
};

type Notebook = {
  cells: NotebookCell[];
  metadata: {
    kernelspec: {
      display_name: string;
      language: string;
      name: string;
    };
    language_info: {
      name: string;
    };
  };
  nbformat: number;
  nbformat_minor: number;
};

const CODE_FENCE = /```(\w+)?\n([\s\S]*?)```/g;

const toSourceLines = (text: string) => {
  const normalized = text.endsWith('\n') ? text : `${text}\n`;
  const lines = normalized.split('\n');
  return lines.map((line, index) =>
    index < lines.length - 1 ? `${line}\n` : line
  );
};

const parseMarkdownToCells = (markdown: string): Array<{ type: 'markdown' | 'code'; content: string }> => {
  const parts: Array<{ type: 'markdown' | 'code'; content: string }> = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = CODE_FENCE.exec(markdown)) !== null) {
    if (match.index > lastIndex) {
      const before = markdown.slice(lastIndex, match.index).trim();
      if (before) {
        parts.push({ type: 'markdown', content: before });
      }
    }
    const code = match[2].replace(/\n$/, '');
    if (code.trim()) {
      parts.push({ type: 'code', content: code });
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < markdown.length) {
    const after = markdown.slice(lastIndex).trim();
    if (after) {
      parts.push({ type: 'markdown', content: after });
    }
  }

  if (parts.length === 0) {
    parts.push({ type: 'markdown', content: markdown.trim() });
  }

  return parts;
};

export const buildLessonFilename = (lesson: LessonResponse, extension: string) => {
  const topicMatch = lesson.objective.match(/^Learn (.+?) at a .+ level in 15 minutes\./i);
  const topic = (topicMatch ? topicMatch[1] : lesson.objective)
    .split(/\s+/)
    .slice(0, 4)
    .join(' ');
  const slug = topic
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 32);
  const date = new Date().toISOString().slice(2, 10).replace(/-/g, '');
  return `ulearn-${slug || 'lesson'}-${date}.${extension}`;
};

export const lessonToNotebook = (lesson: LessonResponse): Notebook => {
  const cells: NotebookCell[] = [];
  const header = `# ${lesson.objective}\n\nTotal time: ${lesson.total_minutes} minutes`;
  cells.push({
    cell_type: 'markdown',
    metadata: {},
    source: toSourceLines(header),
  });

  for (const section of lesson.sections) {
    const sectionHeader = `## ${section.title} (${section.minutes} min)`;
    cells.push({
      cell_type: 'markdown',
      metadata: {},
      source: toSourceLines(sectionHeader),
    });

    const parts = parseMarkdownToCells(section.content_markdown);
    for (const part of parts) {
      if (part.type === 'markdown') {
        cells.push({
          cell_type: 'markdown',
          metadata: {},
          source: toSourceLines(part.content),
        });
      } else {
        cells.push({
          cell_type: 'code',
          metadata: {},
          execution_count: null,
          outputs: [],
          source: toSourceLines(part.content),
        });
      }
    }
  }

  return {
    cells,
    metadata: {
      kernelspec: {
        display_name: 'Python 3',
        language: 'python',
        name: 'python3',
      },
      language_info: {
        name: 'python',
      },
    },
    nbformat: 4,
    nbformat_minor: 5,
  };
};
