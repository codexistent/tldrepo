# 11/11/2026

11:11... what a lucky day to be starting a project!

To kick it off, the first thing I did was to scope (in `SCOPE.md`).

## Scaffolding

The first real decision I had to make was picking the linter. We used `ESLint` cuz its standard.

# 11/12/2026

## Scaffolding, contd.

I encountered my first error today, specifically when installing `shadcn` into my app:

```
✖ Validating import alias.

Could not find valid path aliases or package imports for init.
Configure path aliases in tsconfig.json or imports in package.json, then run init again.
Learn more at https://ui.shadcn.com/docs/installation/manual#configure-import-aliases.
```

This was fixed by adding the following lines to `tsconfig.json`:

```
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Browser-side routing

We also set up browser side routing, rewriting from all paths to `/index.html`.
