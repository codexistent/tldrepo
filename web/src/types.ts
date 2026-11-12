/**
 * @fileoverview defines types used throughout app
 */

// metadata on repo
export type RepoMeta = {
  owner: string;
  repo: string;
  sha: string;
  cached: boolean;
};

export type RepoOverview = {
  summary: string;
  stack: string[];
  entryPoint: string;
};

// a stop along the tour to explore a specific file; cld be better named lol
export type TourStopEvent = {
  index: number;
  title: string;
  path: string;
  startLine: number;
  endLine: number;
  explanation: string; // (50 words max)
  whyItMatters: string; // (25 words max)
};

// event for when stream is complete
export type TourDoneEvent = {
  stopCount: number;
  ms: number;
};

// event for when there is error
export type TourErrorEvent = {
  message: string;
};
