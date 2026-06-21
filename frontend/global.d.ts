// Ambient declarations for global stylesheet side-effect imports such as
// `import "./globals.css"`. Without this, TypeScript reports TS2882
// ("Cannot find module or type declarations for side-effect import") because
// Next.js only ships typings for CSS Modules (`*.module.css`), not plain
// global stylesheets. CSS Modules keep their typed declarations — `*.module.css`
// is a more specific match and still resolves to the Next.js typing.
declare module "*.css";
