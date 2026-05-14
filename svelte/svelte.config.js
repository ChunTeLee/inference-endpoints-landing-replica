import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
export default {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({ fallback: '200.html' }),
    paths: { base: process.env.BASE_PATH || '' },
    prerender: {
      handleHttpError: ({ path, message }) => {
        // /catalog and /new?... are placeholder nav links from the source
        // page — they don't have routes here, just ignore them.
        if (path === '/catalog' || path.startsWith('/new')) return;
        throw new Error(message);
      }
    }
  }
};
