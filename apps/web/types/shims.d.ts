// Temporary shims to quiet the editor until packages are installed.
// Remove this file after running `pnpm install` successfully.

declare module "@tanstack/react-query";
declare module "axios";
declare module "next/dynamic";
declare module "next/navigation";
declare module "react-cytoscapejs";
declare module "react-plotly.js";
declare module "plotly.js-dist-min";
declare module "jspdf";
declare module "html2canvas";
declare module "react";

declare var process: any;

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}
