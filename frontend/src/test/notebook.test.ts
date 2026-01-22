import { describe, it, expect } from 'vitest';
import { buildLessonFilename, lessonToNotebook } from '@/lib/notebook';
import type { LessonResponse } from '@/types/lesson';

describe('notebook export', () => {
  const lesson: LessonResponse = {
    objective: 'Learn pandas groupby at a beginner level in 15 minutes.',
    total_minutes: 15,
    sections: [
      {
        id: 'concept',
        title: 'Concept',
        minutes: 5,
        content_markdown: 'Intro text for concept.',
      },
      {
        id: 'example',
        title: 'Example',
        minutes: 5,
        content_markdown: '```python\nprint("hi")\n```\nSome notes.',
      },
    ],
  };

  it('builds a notebook with markdown and code cells', () => {
    const notebook = lessonToNotebook(lesson);

    expect(notebook.nbformat).toBe(4);
    expect(notebook.cells[0].cell_type).toBe('markdown');
    expect(notebook.cells.some((cell) => cell.cell_type === 'code')).toBe(true);

    const codeCell = notebook.cells.find((cell) => cell.cell_type === 'code');
    expect(codeCell?.source.join('')).toContain('print("hi")');
  });

  it('builds a stable filename with extension', () => {
    const filename = buildLessonFilename(lesson, 'ipynb');
    expect(filename).toMatch(/^ulearn-pandas-groupby-\d{6}\.ipynb$/);
  });
});
