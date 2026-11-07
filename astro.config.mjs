import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://bili186.github.io',
  base: '/GLAW',
  outDir: 'dist',
  build: { inlineStylesheets: 'auto' },
});
