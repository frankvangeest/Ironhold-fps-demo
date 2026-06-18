/* tslint:disable */
/* eslint-disable */

export function start(): void;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly start: () => void;
    readonly wasm_bindgen__closure__destroy__h263192ed2f0d8552: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h0cf766bef76dd6c2: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h3aa634acd7532ef7: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hd8b487dd173c9c27: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h23fb4efb2f2d53e0: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__heb064b6ef277ea06: (a: number, b: number, c: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2088fd7cf3c1c1c5: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hece7a97de041ac92: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hcd88145ad2cfd9f7: (a: number, b: number) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
