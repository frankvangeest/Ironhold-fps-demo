import { execFile } from "node:child_process"
import { join } from "node:path"

const ASSET_CHECK = join("scripts", "check_asset_size.py")

function runAssetCheck(cwd: string): Promise<string> {
  return new Promise((resolve) => {
    execFile(
      "python",
      [ASSET_CHECK],
      { cwd, windowsHide: true, timeout: 60_000 },
      (error, stdout) => {
        if (error || !stdout) return resolve("")
        resolve(stdout.toString().trim())
      },
    )
  })
}

export const IronholdHooks = async ({ client, directory }) => {
  return {
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const message = await runAssetCheck(directory)
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