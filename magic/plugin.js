import { spawn } from "node:child_process";
import { basename, join, resolve } from "node:path";

/**
 * BELENTANI // MAGIC PLUGIN
 * Adds an /immersive command that opens the project's local browser experiment.
 */
export const magic = async ({ project }) => {
  const projectDirectory = resolve(project?.directory || process.cwd());
  const repo = basename(projectDirectory) || "node";

  project.command("immersive", {
    description: "Open the local OmniAgent magic experience",
    async run() {
      const target = join(projectDirectory, "magic", "immersive.html");
      const [executable, args] = process.platform === "win32"
        ? ["explorer.exe", [target]]
        : process.platform === "darwin"
          ? ["open", [target]]
          : ["xdg-open", [target]];

      return new Promise((resolveResult) => {
        const child = spawn(executable, args, {
          detached: true,
          shell: false,
          stdio: "ignore",
        });
        child.once("error", (error) => {
          resolveResult(`Unable to open the local experience: ${error.message}`);
        });
        child.once("spawn", () => {
          child.unref();
          resolveResult(`Opened the local experience for ${repo}.`);
        });
      });
    },
  });

  return () => {};
};
