import { execFile } from "node:child_process"
import { join } from "node:path"

const ASSET_CHECK = join("scripts", "check_asset_size.py")
const RON_CHECK = join("scripts", "validate_changed_ron.py")

function runScript(script: string, cwd: string): Promise<string> {
  return new Promise((resolve) => {
    execFile(
      "python",
      [script],
      { cwd, windowsHide: true, timeout: 60_000 },
      (error, stdout) => {
        if (!stdout) return resolve("") // a failing check exits non-zero but still prints its message
        resolve(stdout.toString().trim())
      },
    )
  })
}

export const IronholdHooks = async ({ client, directory }) => {
  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const message = [await runScript(ASSET_CHECK, directory), await runScript(RON_CHECK, directory)]
        .filter(Boolean)
        .join(String.fromCharCode(10))
      if (!message) return
      try {
        await client.app.log({
          body: {
            service: "ironhold-hooks",
            level: "warn",
            message,
            extra: {},
          },
        })
      } catch {
        console.warn(message)
      }
    },
  }
}