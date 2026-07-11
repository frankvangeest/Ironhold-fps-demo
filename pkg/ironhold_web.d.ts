/* tslint:disable */
/* eslint-disable */

export function start(): void;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly start: () => void;
    readonly wasm_bindgen__closure__destroy__h3aa634acd7532ef7: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h2b499a0c1593c7cf: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h82c63276985f4f1f: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hcb423d0bba76ef53: (a: number, b: number, c: any, d: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h2088fd7cf3c1c1c5: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h28e1d5de3a8e0a26: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h55f4eb0b2118bae2: (a: number, b: number, c: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h18b0c9142ae67750: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hb803a948b7eba3b8: (a: number, b: number) => void;
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
